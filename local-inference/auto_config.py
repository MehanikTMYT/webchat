import os
import subprocess
import platform
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AutoConfig:
    """Класс для автоматической настройки локального инференса"""
    
    def __init__(self):
        self.system_info = self._detect_system_info()
        self.gpu_info = self._detect_gpu_info()
        self.cuda_info = self._detect_cuda_info()
    
    def _detect_system_info(self) -> Dict[str, Any]:
        """Определяет информацию о системе"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "machine": platform.machine(),
            "node": platform.node(),
            "memory_gb": self._get_memory_gb(),
        }
    
    def _get_memory_gb(self) -> float:
        """Получает объем оперативной памяти в ГБ"""
        try:
            if platform.system() == "Windows":
                import psutil
                return round(psutil.virtual_memory().total / (1024**3), 2)
            else:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            total_kb = int(line.split()[1])
                            return round(total_kb / (1024**2), 2)
        except:
            return 0.0
    
    def _detect_gpu_info(self) -> Dict[str, Any]:
        """Определяет информацию о GPU"""
        gpu_info = {
            "vendor": None,
            "model": None,
            "vram_gb": None,
            "cuda_cores": None,
        }
        
        try:
            # Проверяем NVIDIA GPU
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,cores', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(', ')
                if len(gpu_data) >= 2:
                    gpu_info["vendor"] = "NVIDIA"
                    gpu_info["model"] = gpu_data[0].strip()
                    gpu_info["vram_gb"] = float(gpu_data[1].strip()) / 1024  # Convert MB to GB
                    if len(gpu_data) > 2:
                        gpu_info["cuda_cores"] = int(gpu_data[2].strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            # Если nvidia-smi недоступен, проверяем через PyTorch
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info["vendor"] = "NVIDIA"
                    gpu_info["model"] = torch.cuda.get_device_name(0)
                    gpu_info["vram_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            except ImportError:
                pass
            except Exception:
                pass
        
        return gpu_info
    
    def _detect_cuda_info(self) -> Dict[str, Any]:
        """Определяет информацию о CUDA"""
        cuda_info = {
            "available": False,
            "version": None,
            "driver_version": None,
            "compute_capability": None,
        }
        
        try:
            # Проверяем версию CUDA
            result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'release' in line:
                        cuda_info["version"] = line.split('release')[-1].strip().replace(',', '')
                        break
            
            # Определяем compute capability для RTX 4070
            if self.gpu_info.get("model", "").lower().startswith("nvidia rtx 4070"):
                cuda_info["compute_capability"] = "8.9"  # Для Ada Lovelace (RTX 40xx)
                cuda_info["available"] = True
            elif self.gpu_info.get("model", "").lower().startswith("nvidia rtx 30"):
                cuda_info["compute_capability"] = "8.6"  # Для Ampere (RTX 30xx)
                cuda_info["available"] = True
            elif self.gpu_info.get("model", "").lower().startswith("nvidia rtx 20"):
                cuda_info["compute_capability"] = "7.5"  # Для Turing (RTX 20xx)
                cuda_info["available"] = True
            elif self.gpu_info.get("vendor") == "NVIDIA":
                cuda_info["available"] = True
                # Если модель не определена, пытаемся получить через PyTorch
                try:
                    import torch
                    if torch.cuda.is_available():
                        major, minor = torch.cuda.get_device_capability(0)
                        cuda_info["compute_capability"] = f"{major}.{minor}"
                except:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Проверяем через PyTorch
            try:
                import torch
                if torch.cuda.is_available():
                    cuda_info["available"] = True
                    major, minor = torch.cuda.get_device_capability(0)
                    cuda_info["compute_capability"] = f"{major}.{minor}"
            except ImportError:
                pass
            except Exception:
                pass
        
        return cuda_info
    
    def get_optimal_config(self) -> Dict[str, Any]:
        """Возвращает оптимальную конфигурацию для текущей системы"""
        config = {
            "system": self.system_info,
            "gpu": self.gpu_info,
            "cuda": self.cuda_info,
            "inference_settings": {
                "use_tensorrt": self.cuda_info["available"],
                "tensorrt_precision": "fp16" if self.cuda_info["available"] else "fp32",
                "batch_size": self._calculate_batch_size(),
                "max_workers": min(4, os.cpu_count() or 4),
                "precision": "fp16" if self.cuda_info["available"] else "fp32",
            }
        }
        
        # Устанавливаем переменные окружения для оптимизации
        self._set_environment_vars(config)
        
        return config
    
    def _calculate_batch_size(self) -> int:
        """Рассчитывает оптимальный размер батча на основе VRAM"""
        vram_gb = self.gpu_info.get("vram_gb", 0)
        
        if vram_gb >= 12:
            return 8
        elif vram_gb >= 8:
            return 4
        elif vram_gb >= 6:
            return 2
        else:
            return 1
    
    def _set_environment_vars(self, config: Dict[str, Any]):
        """Устанавливает переменные окружения для оптимизации"""
        # Устанавливаем compute capability для CUDA
        if config["cuda"]["compute_capability"]:
            os.environ["CUDA_ARCH"] = config["cuda"]["compute_capability"]
        
        # Устанавливаем флаг использования TensorRT
        os.environ["RUST_CUDA_ARCH"] = config["cuda"]["compute_capability"] if config["cuda"]["available"] else "cpu"
        
        logger.info(f"Environment configured for: {config['gpu']['model'] if config['gpu']['model'] else 'unknown GPU'}")
        logger.info(f"CUDA Compute Capability: {config['cuda']['compute_capability']}")
        logger.info(f"TensorRT enabled: {config['inference_settings']['use_tensorrt']}")


# Функция для получения конфигурации
def get_auto_config() -> Dict[str, Any]:
    """Возвращает автоматически сгенерированную конфигурацию"""
    auto_config = AutoConfig()
    return auto_config.get_optimal_config()


if __name__ == "__main__":
    config = get_auto_config()
    print(json.dumps(config, indent=2, default=str))