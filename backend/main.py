import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


from dotenv import load_dotenv

# Явная загрузка .env файла
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.services.connection_manager import manager, ConnectionMode
from backend.config.network_config import NetworkConfig
from backend.auth.jwt_manager import JWTManager
from backend.auth.offline_verifier import OfflineTokenVerifier


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hybrid Chatbot API Gateway",
    description="API gateway for the hybrid chatbot with adaptive networking",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# JWT Manager
jwt_manager = JWTManager()
token_verifier = OfflineTokenVerifier()

# Network configuration
network_config = NetworkConfig()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Проверяет JWT токен"""
    try:
        payload = token_verifier.verify_token(credentials.credentials)
        return payload
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Hybrid Chatbot API Gateway is running",
        "timestamp": datetime.now().isoformat(),
        "connection_mode": network_config.get_connection_mode(),
        "inference_endpoint": network_config.get_inference_endpoint()
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности API Gateway"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connection_mode": network_config.get_connection_mode(),
        "active_connections": len(manager.active_connections),
        "network_config": {
            "local_ip": network_config.detect_local_ip(),
            "inference_endpoint": network_config.get_inference_endpoint()
        }
    }


@app.post("/auth/login")
async def login(username: str, password: str):
    """Аутентификация пользователя"""
    # В реальной реализации здесь будет проверка учетных данных
    # Пока просто создаем токен для демонстрации
    if username and password:  # Простая проверка для демонстрации
        token = jwt_manager.create_token({"username": username, "exp": datetime.utcnow() + timedelta(hours=24)})
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint для реального времени общения"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.handle_client_message(client_id, data)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")


@app.get("/network/config")
async def get_network_config():
    """Возвращает текущую конфигурацию сети"""
    return {
        "local_ip": network_config.detect_local_ip(),
        "connection_mode": network_config.get_connection_mode(),
        "inference_endpoint": network_config.get_inference_endpoint(),
        "network_detection_time": datetime.now().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """Действия при запуске приложения"""
    logger.info("Starting Hybrid Chatbot API Gateway...")
    
    # Выполняем первоначальную настройку, если это первый запуск
    from backend.first_run_setup import FirstRunSetup
    setup = FirstRunSetup()
    setup.run_setup()
    
    logger.info(f"Network configuration: {network_config.get_connection_mode()}")
    logger.info(f"Inference endpoint: {network_config.get_inference_endpoint()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Действия при выключении приложения"""
    logger.info("Shutting down Hybrid Chatbot API Gateway...")


if __name__ == "__main__":
    port = int(os.getenv('API_GATEWAY_PORT', '8000'))
    host = os.getenv('API_GATEWAY_HOST', '0.0.0.0')
    
    logger.info(f"Starting API Gateway on {host}:{port}")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )