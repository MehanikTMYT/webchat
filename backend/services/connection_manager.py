import asyncio
import json
from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum


class ConnectionMode(str, Enum):
    DIRECT = "direct"
    RELAY = "relay"
    OFFLINE = "offline"
    HYBRID = "hybrid"


class ConnectionManager:
    """Класс для управления WebSocket-подключениями и адаптивной сетью"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_modes: Dict[str, ConnectionMode] = {}
        self.client_sessions: Dict[str, dict] = {}
        self.reconnect_attempts: Dict[str, int] = {}
        self.max_reconnect_attempts = int(
            self._get_env_var("MAX_RECONNECT_ATTEMPTS", "10")
        )
        self.reconnect_delay = int(
            self._get_env_var("RECONNECT_DELAY", "5")
        )
    
    def _get_env_var(self, key: str, default: str) -> str:
        """Получает переменную окружения или возвращает значение по умолчанию"""
        import os
        return os.getenv(key, default)
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Подключение нового клиента"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_sessions[client_id] = {
            'connected_at': asyncio.get_event_loop().time(),
            'last_message': None,
            'session_data': {}
        }
        
        # Определяем режим подключения для этого клиента
        from backend.config.network_config import NetworkConfig
        mode = NetworkConfig.get_connection_mode()
        self.connection_modes[client_id] = ConnectionMode(mode)
        
        print(f"Client {client_id} connected with mode: {mode}")
    
    def disconnect(self, client_id: str):
        """Отключение клиента"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_modes:
            del self.connection_modes[client_id]
        if client_id in self.client_sessions:
            del self.client_sessions[client_id]
        if client_id in self.reconnect_attempts:
            del self.reconnect_attempts[client_id]
    
    async def send_personal_message(self, message: str, client_id: str):
        """Отправка личного сообщения клиенту"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(client_id)
    
    async def broadcast(self, message: str):
        """Рассылка сообщения всем подключенным клиентам"""
        disconnected_clients = []
        
        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
        
        # Отключаем разорвавшиеся соединения
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    def get_connection_mode(self, client_id: str) -> Optional[ConnectionMode]:
        """Получить режим подключения для конкретного клиента"""
        return self.connection_modes.get(client_id)
    
    def get_client_session(self, client_id: str) -> Optional[dict]:
        """Получить сессионные данные клиента"""
        return self.client_sessions.get(client_id)
    
    async def handle_client_message(self, client_id: str, data: str):
        """Обработка сообщения от клиента с учетом режима подключения"""
        try:
            message_data = json.loads(data)
            
            # Обновляем информацию о последнем сообщении
            if client_id in self.client_sessions:
                self.client_sessions[client_id]['last_message'] = message_data
            
            # Определяем, как обрабатывать сообщение в зависимости от режима
            mode = self.get_connection_mode(client_id)
            
            if mode == ConnectionMode.OFFLINE:
                # В оффлайн-режиме обрабатываем локально
                response = await self._handle_offline_request(message_data)
            elif mode in [ConnectionMode.DIRECT, ConnectionMode.RELAY]:
                # В других режимах отправляем запрос на inference
                response = await self._forward_to_inference(message_data, mode)
            else:
                # По умолчанию используем relay
                response = await self._forward_to_inference(message_data, ConnectionMode.RELAY)
            
            # Отправляем ответ клиенту
            await self.send_personal_message(json.dumps(response), client_id)
            
        except json.JSONDecodeError:
            error_response = {"error": "Invalid JSON", "type": "parse_error"}
            await self.send_personal_message(json.dumps(error_response), client_id)
        except Exception as e:
            error_response = {"error": str(e), "type": "processing_error"}
            await self.send_personal_message(json.dumps(error_response), client_id)
    
    async def _handle_offline_request(self, message_data: dict) -> dict:
        """Обработка запроса в оффлайн-режиме"""
        # В оффлайн-режиме возвращаем предопределенное сообщение или кэшированный ответ
        return {
            "response": "Работаю в оффлайн-режиме. Соединение с инференс-сервером недоступно.",
            "status": "offline",
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def _forward_to_inference(self, message_data: dict, mode: ConnectionMode) -> dict:
        """Пересылка запроса на инференс-сервер"""
        import requests
        from backend.config.network_config import NetworkConfig
        
        try:
            # Получаем endpoint для инференса
            inference_url = f"{NetworkConfig.get_inference_endpoint()}/generate"
            
            # Отправляем запрос на инференс-сервер
            response = requests.post(
                inference_url,
                json=message_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Inference server error: {response.status_code}",
                    "status": "error",
                    "timestamp": asyncio.get_event_loop().time()
                }
        except requests.exceptions.ConnectionError:
            # Если не можем подключиться, пробуем переподключиться
            return await self._handle_connection_failure(message_data, mode)
        except Exception as e:
            return {
                "error": f"Request to inference failed: {str(e)}",
                "status": "error",
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def _handle_connection_failure(self, message_data: dict, mode: ConnectionMode) -> dict:
        """Обработка сбоя подключения к инференс-серверу"""
        # Увеличиваем счетчик попыток переподключения
        client_id = self._find_client_by_mode(mode)
        if client_id:
            self.reconnect_attempts[client_id] = self.reconnect_attempts.get(client_id, 0) + 1
            
            if self.reconnect_attempts[client_id] >= self.max_reconnect_attempts:
                # Если достигли максимального количества попыток, переходим в оффлайн-режим
                self.connection_modes[client_id] = ConnectionMode.OFFLINE
                return {
                    "response": "Превышено максимальное количество попыток подключения. Переход в оффлайн-режим.",
                    "status": "offline",
                    "attempts": self.reconnect_attempts[client_id]
                }
            else:
                # Пытаемся переподключиться
                await asyncio.sleep(self.reconnect_delay)
                
                # Обновляем режим подключения
                from backend.config.network_config import NetworkConfig
                new_mode = NetworkConfig.get_connection_mode()
                if client_id:
                    self.connection_modes[client_id] = ConnectionMode(new_mode)
                
                # Повторяем запрос
                return await self._forward_to_inference(message_data, ConnectionMode(new_mode))
        
        return {
            "error": "Connection failure and unable to identify client",
            "status": "error"
        }
    
    def _find_client_by_mode(self, mode: ConnectionMode) -> Optional[str]:
        """Находит ID клиента по режиму подключения"""
        for client_id, conn_mode in self.connection_modes.items():
            if conn_mode == mode:
                return client_id
        return None


# Глобальный экземпляр менеджера соединений
manager = ConnectionManager()