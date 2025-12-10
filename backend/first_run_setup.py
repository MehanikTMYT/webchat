import os
import secrets
import hashlib
from pathlib import Path


class FirstRunSetup:
    """Класс для автоматической настройки при первом запуске"""
    
    def __init__(self, config_path: str = ".env"):
        self.config_path = config_path
        self.is_first_run = not os.path.exists("backend_initialized")
    
    def generate_secret_key(self) -> str:
        """Генерирует секретный ключ для JWT"""
        return secrets.token_urlsafe(32)
    
    def generate_api_keys(self) -> tuple:
        """Генерирует API-ключи для внутреннего использования"""
        admin_key = secrets.token_urlsafe(32)
        service_key = secrets.token_urlsafe(32)
        return admin_key, service_key
    
    def update_env_file(self):
        """Обновляет .env файл с сгенерированными значениями"""
        env_path = Path(self.config_path)
        
        # Читаем существующий .env файл или создаем новый
        if env_path.exists():
            content = env_path.read_text(encoding='utf-8')
        else:
            content = ""
        
        # Генерируем значения
        jwt_secret = self.generate_secret_key()
        admin_api_key, service_api_key = self.generate_api_keys()
        
        # Проверяем, есть ли уже JWT_SECRET в файле
        if 'JWT_SECRET=' not in content:
            content += f"\n# Секретный ключ для JWT (сгенерирован автоматически)\n"
            content += f"JWT_SECRET={jwt_secret}\n"
        
        if 'ADMIN_API_KEY=' not in content:
            content += f"\n# API ключи для внутреннего использования\n"
            content += f"ADMIN_API_KEY={admin_api_key}\n"
            content += f"SERVICE_API_KEY={service_api_key}\n"
        
        # Записываем обновленный контент
        env_path.write_text(content, encoding='utf-8')
        
        print(f"Обновлен файл конфигурации: {self.config_path}")
        print(f"JWT_SECRET и API-ключи сгенерированы и добавлены в {self.config_path}")
    
    def detect_network_config(self):
        """Определяет сетевые параметры и обновляет конфигурацию"""
        from backend.config.network_config import NetworkConfig
        
        # Определяем локальный IP
        local_ip = NetworkConfig.detect_local_ip()
        
        # Проверяем и обновляем .env файл
        env_path = Path(self.config_path)
        content = env_path.read_text(encoding='utf-8') if env_path.exists() else ""
        
        # Обновляем LOCAL_INFERENCE_IP, если он равен auto_detect
        if 'LOCAL_INFERENCE_IP=auto_detect' in content:
            content = content.replace('LOCAL_INFERENCE_IP=auto_detect', f'LOCAL_INFERENCE_IP={local_ip}')
            env_path.write_text(content, encoding='utf-8')
            print(f"LOCAL_INFERENCE_IP установлен в {local_ip}")
    
    def create_directories(self):
        """Создает необходимые директории"""
        directories = [
            "logs",
            "data",
            "uploads",
            "models",  # Для локального ПК
            "cache"
        ]
        
        for directory in directories:
            path = Path(directory)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                print(f"Создана директория: {directory}")
    
    def initialize_database(self):
        """Инициализирует базу данных (заглушка, будет реализована позже)"""
        print("Инициализация базы данных...")
        # Здесь будет логика инициализации базы данных
        # Пока просто создаем файл-маркер
        db_path = Path("data/database.db")  # для SQLite
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Создаем файл-маркер инициализации
        Path("backend_initialized").touch()
        print("База данных инициализирована")
    
    def run_setup(self):
        """Выполняет полную процедуру первоначальной настройки"""
        if not self.is_first_run:
            print("Настройка уже была выполнена ранее")
            return
        
        print("Запуск первоначальной настройки...")
        
        # 1. Создаем необходимые директории
        self.create_directories()
        
        # 2. Обновляем .env файл с сгенерированными ключами
        self.update_env_file()
        
        # 3. Определяем сетевые параметры
        self.detect_network_config()
        
        # 4. Инициализируем базу данных
        self.initialize_database()
        
        print("Первоначальная настройка завершена!")
        print("Сгенерированные ключи сохранены в .env файл")


if __name__ == "__main__":
    setup = FirstRunSetup()
    setup.run_setup()