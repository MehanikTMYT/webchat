import os
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_secret_key() -> str:
    """Получает или генерирует секретный ключ"""
    secret = os.getenv('JWT_SECRET')
    
    if not secret or secret == 'auto_generate':
        # Генерируем новый секретный ключ
        secret = secrets.token_urlsafe(32)
        # В реальной реализации нужно сохранить его в безопасное место
        logger.info("Generated new JWT secret key")
    
    return secret


class JWTManager:
    """Класс для управления JWT токенами"""
    
    def __init__(self):
        self.secret_key = get_secret_key()
        self.algorithm = "HS256"
    
    def create_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Создает JWT токен"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # По умолчанию токен действителен 24 часа
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверяет JWT токен"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Обновляет токен"""
        payload = self.verify_token(token)
        
        if payload:
            # Удаляем время истечения из исходного payload для создания нового
            if "exp" in payload:
                del payload["exp"]
            
            # Создаем новый токен с новым сроком действия
            new_token = self.create_token(
                payload, 
                expires_delta=timedelta(hours=24)
            )
            return new_token
        
        return None


# Глобальный экземпляр для использования в других модулях
jwt_manager = JWTManager()