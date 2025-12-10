import asyncio
import time
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthChecker:
    """Класс для проверки работоспособности локального инференса"""
    
    def __init__(self):
        self.start_time = time.time()
        self.check_results = {}
    
    async def check_model_health(self) -> Dict[str, Any]:
        """Проверяет работоспособность модели"""
        from local_inference.model_loader import get_model_loader
        
        start_time = time.time()
        model_loader = get_model_loader()
        
        try:
            # Выполняем короткую генерацию для проверки
            test_result = model_loader.generate("health check", max_length=5)
            
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "model_loaded": True,
                "cuda_available": model_loader.is_cuda_available(),
                "using_rust": model_loader.use_rust,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Model health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_loaded": False,
                "response_time": time.time() - start_time,
                "last_check": datetime.now().isoformat()
            }
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Проверяет системные ресурсы"""
        import psutil
        import os
        
        try:
            # Получаем информацию о системе
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Проверяем температуру (если доступна)
            temp_info = {}
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Берем температуру CPU, если доступна
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            temp_info = {name: [f"{e.label or 'temp'}: {e.current}°C" for e in entries]}
                            break
            
            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "temperature": temp_info,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def check_gpu_health(self) -> Dict[str, Any]:
        """Проверяет работоспособность GPU"""
        try:
            import torch
            
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_info = []
                
                for i in range(gpu_count):
                    gpu_properties = torch.cuda.get_device_properties(i)
                    memory_allocated = torch.cuda.memory_allocated(i)
                    memory_reserved = torch.cuda.memory_reserved(i)
                    
                    gpu_info.append({
                        "id": i,
                        "name": gpu_properties.name,
                        "compute_capability": f"{gpu_properties.major}.{gpu_properties.minor}",
                        "memory_gb": round(gpu_properties.total_memory / (1024**3), 2),
                        "memory_allocated_mb": round(memory_allocated / (1024**2), 2),
                        "memory_reserved_mb": round(memory_reserved / (1024**2), 2),
                        "utilization_percent": torch.cuda.utilization(i) if hasattr(torch.cuda, 'utilization') else "N/A"
                    })
                
                return {
                    "status": "healthy",
                    "gpu_count": gpu_count,
                    "gpus": gpu_info,
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "warning",
                    "message": "CUDA not available",
                    "gpu_count": 0,
                    "last_check": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"GPU health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def check_rust_health(self) -> Dict[str, Any]:
        """Проверяет работоспособность Rust-модуля"""
        try:
            import chatbot_inference
            
            # Создаем тестовый движок
            test_engine = chatbot_inference.RustInferenceEngine("./test_model", False)
            
            # Проверяем статистику
            stats = test_engine.get_performance_stats()
            
            return {
                "status": "healthy",
                "available": True,
                "performance_stats": dict(stats),
                "last_check": datetime.now().isoformat()
            }
        except ImportError:
            return {
                "status": "warning",
                "available": False,
                "message": "Rust module not available, using fallback",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Rust health check failed: {e}")
            return {
                "status": "unhealthy",
                "available": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def check_health(self) -> Dict[str, Any]:
        """Полная проверка работоспособности"""
        # Запускаем все проверки параллельно
        results = await asyncio.gather(
            self.check_model_health(),
            self.check_system_health(),
            self.check_gpu_health(),
            self.check_rust_health(),
            return_exceptions=True
        )
        
        # Формируем общий отчет
        health_report = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "checks": {
                "model": results[0] if not isinstance(results[0], Exception) else {"status": "error", "error": str(results[0])},
                "system": results[1] if not isinstance(results[1], Exception) else {"status": "error", "error": str(results[1])},
                "gpu": results[2] if not isinstance(results[2], Exception) else {"status": "error", "error": str(results[2])},
                "rust": results[3] if not isinstance(results[3], Exception) else {"status": "error", "error": str(results[3])},
            }
        }
        
        # Определяем общий статус
        for check_name, check_result in health_report["checks"].items():
            if isinstance(check_result, dict) and check_result.get("status") in ["unhealthy", "error"]:
                health_report["overall_status"] = "unhealthy"
                break
            elif isinstance(check_result, dict) and check_result.get("status") == "warning":
                if health_report["overall_status"] == "healthy":
                    health_report["overall_status"] = "warning"
        
        return health_report
    
    async def perform_detailed_diagnostics(self) -> Dict[str, Any]:
        """Выполняет детальную диагностику системы"""
        from local_inference.auto_config import get_auto_config
        
        config = get_auto_config()
        
        # Выполняем тестовую генерацию с разными параметрами
        from local_inference.model_loader import get_model_loader
        model_loader = get_model_loader()
        
        performance_tests = []
        
        # Тест с разной длиной генерации
        for max_length in [10, 50, 100]:
            start_time = time.time()
            try:
                result = model_loader.generate("Test prompt for performance", max_length=max_length)
                processing_time = time.time() - start_time
                
                performance_tests.append({
                    "max_length": max_length,
                    "processing_time": processing_time,
                    "result_length": len(result),
                    "status": "success"
                })
            except Exception as e:
                performance_tests.append({
                    "max_length": max_length,
                    "processing_time": time.time() - start_time,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "diagnostics": {
                "system_config": config,
                "performance_tests": performance_tests,
                "timestamp": datetime.now().isoformat()
            }
        }