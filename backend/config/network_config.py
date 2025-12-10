import socket
import requests
import os
from typing import Optional


class NetworkConfig:
    """Класс для автоматического определения сетевых параметров"""
    
    @staticmethod
    def detect_local_ip() -> str:
        """
        Определяет локальный IP-адрес машины
        Возвращает IP-адрес или fallback значение
        """
        try:
            # Определение внешнего IP через сервис
            try:
                public_ip = requests.get('https://api.ipify.org?format=json', timeout=3).json()['ip']
            except:
                public_ip = None
            
            # Определение локального IP для LAN
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Подключение к внешнему адресу для определения локального IP
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            except Exception:
                local_ip = "127.0.0.1"
            finally:
                s.close()
            
            # Возвращаем локальный IP, если он является частным (LAN)
            if public_ip and not NetworkConfig._is_private_ip(public_ip):
                return public_ip
            return local_ip
        except:
            return "192.168.1.100"  # fallback
    
    @staticmethod
    def _is_private_ip(ip: str) -> bool:
        """Проверяет, является ли IP частным (локальным)"""
        return (
            ip.startswith(('10.', '172.', '192.168.')) or
            ip.startswith('127.') or  # localhost
            ip.startswith('169.254.')  # link-local
        )
    
    @staticmethod
    def get_connection_mode() -> str:
        """
        Определяет режим подключения на основе доступности сервисов
        Возвращает: 'direct', 'relay', 'offline', 'hybrid'
        """
        # Проверяем, запущен ли локальный inference сервер
        local_inference_ip = os.getenv('LOCAL_INFERENCE_IP', 'auto_detect')
        if local_inference_ip == 'auto_detect':
            local_inference_ip = NetworkConfig.detect_local_ip()
        
        local_inference_port = os.getenv('LOCAL_INFERENCE_PORT', '8001')
        
        # Пытаемся подключиться к локальному inference серверу
        try:
            import requests
            response = requests.get(f"http://{local_inference_ip}:{local_inference_port}/health", timeout=2)
            if response.status_code == 200:
                return 'direct'  # Прямое подключение к локальному ПК
        except:
            pass
        
        # Если не можем подключиться напрямую, используем relay через VDS
        return 'relay'
    
    @staticmethod
    def get_inference_endpoint() -> str:
        """Возвращает endpoint для инференса на основе определенного режима подключения"""
        mode = NetworkConfig.get_connection_mode()
        
        if mode == 'direct':
            local_ip = os.getenv('LOCAL_INFERENCE_IP', 'auto_detect')
            if local_ip == 'auto_detect':
                local_ip = NetworkConfig.detect_local_ip()
            port = os.getenv('LOCAL_INFERENCE_PORT', '8001')
            return f"http://{local_ip}:{port}"
        else:
            # В режиме relay используем VDS как посредника
            return f"http://127.0.0.1:{os.getenv('LOCAL_INFERENCE_PORT', '8001')}"