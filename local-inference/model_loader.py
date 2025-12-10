import os
import sys
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RustModelLoader:
    """
    Загрузчик модели с поддержкой Rust-оптимизации и fallback на Python
    """
    
    def __init__(self):
        self.rust_engine = None
        self.fallback_engine = None
        self.use_rust = self._should_use_rust()
        self._initialize_engines()
    
    def _should_use_rust(self) -> bool:
        """Определяет, использовать ли Rust-оптимизацию"""
        rust_acceleration = os.getenv('RUST_ACCELERATION', 'true').lower() == 'true'
        
        if not rust_acceleration:
            logger.info("Rust acceleration disabled by environment variable")
            return False
        
        try:
            # Проверяем, можно ли импортировать Rust-модуль
            import chatbot_inference
            return True
        except ImportError:
            logger.warning("Rust module not available, using fallback engine")
            return False
        except Exception as e:
            logger.warning(f"Error importing Rust module: {e}, using fallback engine")
            return False
    
    def _initialize_engines(self):
        """Инициализирует Rust и Python движки"""
        if self.use_rust:
            try:
                import chatbot_inference
                # Определяем архитектуру CUDA
                cuda_arch = os.getenv('RUST_CUDA_ARCH', 'auto')
                use_tensorrt = cuda_arch != 'cpu'
                
                model_path = os.getenv('MODEL_PATH', './models/default_model')
                
                self.rust_engine = chatbot_inference.RustInferenceEngine(
                    model_path, 
                    use_tensorrt
                )
                
                logger.info("Rust inference engine initialized successfully")
                
                # Выводим статистику производительности
                if hasattr(self.rust_engine, 'get_performance_stats'):
                    stats = self.rust_engine.get_performance_stats()
                    logger.info(f"Rust engine stats: {dict(stats)}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Rust engine: {e}")
                self.use_rust = False
                self._initialize_fallback_engine()
        else:
            self._initialize_fallback_engine()
    
    def _initialize_fallback_engine(self):
        """Инициализирует Python fallback-движок"""
        try:
            from local_inference.fallback_engine import PythonInferenceEngine
            self.fallback_engine = PythonInferenceEngine()
            logger.info("Python fallback engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize fallback engine: {e}")
            raise
    
    def generate(self, input_text: str, max_length: int = 100) -> str:
        """Генерация текста с использованием доступного движка"""
        if self.use_rust and self.rust_engine:
            try:
                return self.rust_engine.generate(input_text, max_length)
            except Exception as e:
                logger.error(f"Rust engine failed: {e}")
                # Переключаемся на fallback
                self.use_rust = False
                return self._generate_with_fallback(input_text, max_length)
        else:
            return self._generate_with_fallback(input_text, max_length)
    
    def _generate_with_fallback(self, input_text: str, max_length: int) -> str:
        """Генерация с использованием fallback-движка"""
        if self.fallback_engine:
            return self.fallback_engine.generate(input_text, max_length)
        else:
            raise RuntimeError("No available inference engine")
    
    def is_cuda_available(self) -> bool:
        """Проверяет доступность CUDA"""
        if self.use_rust and self.rust_engine:
            try:
                return self.rust_engine.is_cuda_available()
            except:
                return False
        else:
            return self.fallback_engine.is_cuda_available() if self.fallback_engine else False


# Глобальный экземпляр для использования в других модулях
model_loader = RustModelLoader()


def get_model_loader() -> RustModelLoader:
    """Возвращает экземпляр загрузчика модели"""
    return model_loader