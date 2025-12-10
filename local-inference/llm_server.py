import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from local_inference.model_loader import get_model_loader
from local_inference.health_check import HealthChecker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local LLM Inference Server",
    description="High-performance local LLM inference server with Rust optimization",
    version="1.0.0"
)

# Загружаем модель
model_loader = get_model_loader()

# Создаем health checker
health_checker = HealthChecker()


class GenerateRequest(BaseModel):
    prompt: str
    max_length: int = 100
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50


class GenerateResponse(BaseModel):
    generated_text: str
    model_info: Dict[str, Any]
    processing_time: float
    timestamp: str


@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работоспособности сервера"""
    return {
        "message": "Local LLM Inference Server is running",
        "timestamp": datetime.now().isoformat(),
        "cuda_available": model_loader.is_cuda_available()
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервера"""
    health_status = await health_checker.check_health()
    return health_status


@app.post("/generate", response_model=GenerateResponse)
async def generate_text(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Генерация текста с использованием локальной модели"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Выполняем генерацию текста
        generated_text = model_loader.generate(
            request.prompt, 
            request.max_length
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        # Собираем информацию о модели
        model_info = {
            "cuda_available": model_loader.is_cuda_available(),
            "using_rust": hasattr(model_loader, 'rust_engine') and model_loader.rust_engine is not None
        }
        
        response = GenerateResponse(
            generated_text=generated_text,
            model_info=model_info,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Generated text in {processing_time:.2f}s")
        
        return response
    
    except Exception as e:
        logger.error(f"Error during text generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.get("/config")
async def get_config():
    """Возвращает текущую конфигурацию сервера"""
    from local_inference.auto_config import get_auto_config
    config = get_auto_config()
    
    return {
        "config": config,
        "environment": {
            "cuda_arch": os.getenv("CUDA_ARCH", "not set"),
            "rust_cuda_arch": os.getenv("RUST_CUDA_ARCH", "not set"),
            "rust_acceleration": os.getenv("RUST_ACCELERATION", "true"),
        },
        "model_loader_status": {
            "using_rust": model_loader.use_rust,
            "cuda_available": model_loader.is_cuda_available()
        }
    }


@app.on_event('startup')
async def startup_event():
    """Действия при запуске сервера"""
    logger.info("Starting Local LLM Inference Server...")
    logger.info(f"CUDA available: {model_loader.is_cuda_available()}")
    logger.info(f"Using Rust optimization: {model_loader.use_rust}")
    
    # Выполняем тестовую генерацию для проверки работоспособности
    try:
        test_result = model_loader.generate("Hello, world!", max_length=10)
        logger.info(f"Model test successful: {test_result[:50]}...")
    except Exception as e:
        logger.error(f"Model test failed: {e}")


@app.on_event('shutdown')
async def shutdown_event():
    """Действия при выключении сервера"""
    logger.info("Shutting down Local LLM Inference Server...")


if __name__ == "__main__":
    # Запускаем сервер с настройками из переменных окружения
    port = int(os.getenv('LOCAL_INFERENCE_PORT', '8001'))
    host = os.getenv('LOCAL_INFERENCE_HOST', '0.0.0.0')
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "local-inference.llm_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )