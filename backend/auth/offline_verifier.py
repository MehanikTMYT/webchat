import os
import jwt
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_secret_key() -> str:
    """Получает или генерирует секретный ключ (такой же как в JWTManager)"""
    secret = os.getenv('JWT_SECRET')
    
    if not secret or secret == 'auto_generate':
        # Генерируем новый секретный ключ для демо-режима
        import secrets
        secret = secrets.token_urlsafe(32)
        logger.info("Generated temporary JWT secret key for offline verification")
        # В реальной реализации здесь нужно будет обеспечить надежное хранение ключа
    
    return secret


class OfflineTokenVerifier:
    """Класс для оффлайн-проверки JWT токенов"""
    
    def __init__(self):
        self.secret_key = get_secret_key()
        self.algorithm = "HS256"
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет JWT токен без обращения к внешним сервисам
        Возвращает payload токена или None, если токен недействителен
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}  # Проверяем срок действия
            )
            
            # Проверяем дополнительные поля, если необходимо
            if self._validate_payload(payload):
                return payload
            else:
                logger.warning("Token payload validation failed")
                return None
                
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            return None
    
    def _validate_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Проверяет дополнительные поля в payload токена
        В реальной реализации здесь могут быть дополнительные проверки
        """
        # Проверяем, что обязательные поля присутствуют
        required_fields = ['exp']  # Время истечения обязательно
        
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Required field '{field}' missing from token payload")
                return False
        
        # Проверяем, что exp - это число (timestamp)
        if not isinstance(payload['exp'], (int, float)):
            logger.warning("Invalid 'exp' field in token payload")
            return False
        
        return True
    
    def is_token_valid(self, token: str) -> bool:
        """Проверяет, действителен ли токен"""
        return self.verify_token(token) is not None


# Глобальный экземпляр для использования в других модулях
offline_verifier = OfflineTokenVerifier()