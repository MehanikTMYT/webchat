import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4


from dotenv import load_dotenv

# Явная загрузка .env файла
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

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


# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class CreateSessionRequest(BaseModel):
    title: str = "Новый чат"


class UpdateSessionRequest(BaseModel):
    title: str


class SendMessageRequest(BaseModel):
    session_id: str
    message: str


class RegenerateRequest(BaseModel):
    session_id: str
    message_id: str


class UpdateMessageRequest(BaseModel):
    content: str


# Simple in-memory storage for demonstration
users_db = {}
sessions_db = {}
messages_db = {}


def get_user_by_username(username: str):
    """Simple user lookup for demo purposes"""
    return users_db.get(username)


def create_user(username: str, password: str):
    """Simple user creation for demo purposes"""
    user_id = str(uuid4())
    users_db[username] = {
        "id": user_id,
        "username": username,
        "password": password,  # In real app, hash the password
        "created_at": datetime.now().isoformat()
    }
    return users_db[username]


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Проверяет JWT токен"""
    try:
        payload = token_verifier.verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
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
async def login(request: LoginRequest):
    """Аутентификация пользователя"""
    user = get_user_by_username(request.username)
    
    if user and user["password"] == request.password:  # In real app, verify hashed password
        token = jwt_manager.create_token({
            "user_id": user["id"],
            "username": user["username"], 
            "exp": datetime.utcnow() + timedelta(hours=24)
        })
        return {"access_token": token, "token_type": "bearer", "user": user}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/auth/register")
async def register(request: RegisterRequest):
    """Регистрация нового пользователя"""
    if get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = create_user(request.username, request.password)
    token = jwt_manager.create_token({
        "user_id": user["id"],
        "username": user["username"], 
        "exp": datetime.utcnow() + timedelta(hours=24)
    })
    
    return {"access_token": token, "token_type": "bearer", "user": user}


@app.get("/auth/verify")
async def verify_token_endpoint(payload: Dict[str, Any] = Depends(verify_token)):
    """Проверка валидности токена"""
    return {"user": {"username": payload.get("username"), "id": payload.get("user_id")}}


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


# Chat Session Endpoints
@app.get("/api/sessions")
async def get_sessions(payload: Dict[str, Any] = Depends(verify_token)):
    """Получить все сессии чата для текущего пользователя"""
    username = payload.get("username")
    user_sessions = []
    
    for session_id, session in sessions_db.items():
        if session.get("user_id") == payload.get("user_id"):
            user_sessions.append(session)
    
    # Сортируем по дате обновления
    user_sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return user_sessions


@app.post("/api/sessions")
async def create_session(request: CreateSessionRequest, payload: Dict[str, Any] = Depends(verify_token)):
    """Создать новую сессию чата"""
    session_id = str(uuid4())
    timestamp = datetime.now().isoformat()
    
    session = {
        "id": session_id,
        "user_id": payload.get("user_id"),
        "title": request.title,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    sessions_db[session_id] = session
    
    return session


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, payload: Dict[str, Any] = Depends(verify_token)):
    """Получить конкретную сессию"""
    session = sessions_db.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session


@app.put("/api/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest, payload: Dict[str, Any] = Depends(verify_token)):
    """Обновить сессию"""
    session = sessions_db.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    session["title"] = request.title
    session["updated_at"] = datetime.now().isoformat()
    
    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, payload: Dict[str, Any] = Depends(verify_token)):
    """Удалить сессию и связанные сообщения"""
    session = sessions_db.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Удаляем все сообщения этой сессии
    messages_to_delete = []
    for msg_id, msg in messages_db.items():
        if msg.get("session_id") == session_id:
            messages_to_delete.append(msg_id)
    
    for msg_id in messages_to_delete:
        del messages_db[msg_id]
    
    # Удаляем саму сессию
    del sessions_db[session_id]
    
    return {"success": True}


# Message Endpoints
@app.get("/api/sessions/{session_id}/messages")
async def get_messages(session_id: str, payload: Dict[str, Any] = Depends(verify_token)):
    """Получить все сообщения для сессии"""
    session = sessions_db.get(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    session_messages = []
    for msg_id, message in messages_db.items():
        if message.get("session_id") == session_id:
            session_messages.append(message)
    
    # Сортируем по времени создания
    session_messages.sort(key=lambda x: x.get("created_at", ""))
    return session_messages


@app.post("/api/chat/send")
async def send_message(request: SendMessageRequest, payload: Dict[str, Any] = Depends(verify_token)):
    """Отправить сообщение и получить ответ от бота"""
    session = sessions_db.get(request.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Сохраняем сообщение пользователя
    user_msg_id = str(uuid4())
    timestamp = datetime.now().isoformat()
    
    user_message = {
        "id": user_msg_id,
        "session_id": request.session_id,
        "role": "user",
        "content": request.message,
        "created_at": timestamp
    }
    
    messages_db[user_msg_id] = user_message
    
    # Генерируем ответ от бота (в реальном приложении здесь вызов LLM)
    bot_response = generate_bot_response(request.message)
    
    # Сохраняем ответ бота
    bot_msg_id = str(uuid4())
    
    bot_message = {
        "id": bot_msg_id,
        "session_id": request.session_id,
        "role": "assistant",
        "content": bot_response,
        "created_at": datetime.now().isoformat()
    }
    
    messages_db[bot_msg_id] = bot_message
    
    # Обновляем время обновления сессии
    session["updated_at"] = timestamp
    
    return {"response": bot_response}


@app.post("/api/chat/regenerate")
async def regenerate_response(request: RegenerateRequest, payload: Dict[str, Any] = Depends(verify_token)):
    """Перегенерировать последний ответ"""
    session = sessions_db.get(request.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Находим сообщение пользователя, которое нужно перегенерировать
    user_message = messages_db.get(request.message_id)
    
    if not user_message or user_message.get("role") != "user":
        raise HTTPException(status_code=404, detail="User message not found")
    
    # Удаляем старый ответ бота (находим последний ответ после этого сообщения)
    session_messages = []
    for msg_id, msg in messages_db.items():
        if msg.get("session_id") == request.session_id:
            session_messages.append(msg)
    
    # Сортируем по времени создания
    session_messages.sort(key=lambda x: x.get("created_at", ""))
    
    # Находим позицию пользовательского сообщения и следующее за ним сообщение бота
    user_msg_index = -1
    for i, msg in enumerate(session_messages):
        if msg["id"] == request.message_id:
            user_msg_index = i
            break
    
    if user_msg_index != -1 and user_msg_index + 1 < len(session_messages):
        next_msg = session_messages[user_msg_index + 1]
        if next_msg.get("role") == "assistant":
            # Удаляем старый ответ бота
            del messages_db[next_msg["id"]]
    
    # Генерируем новый ответ
    new_response = generate_bot_response(user_message["content"])
    
    # Создаем новое сообщение бота
    new_bot_msg_id = str(uuid4())
    
    new_bot_message = {
        "id": new_bot_msg_id,
        "session_id": request.session_id,
        "role": "assistant",
        "content": new_response,
        "created_at": datetime.now().isoformat()
    }
    
    messages_db[new_bot_msg_id] = new_bot_message
    
    return {"response": new_response}


@app.put("/api/messages/{message_id}")
async def update_message(message_id: str, request: UpdateMessageRequest, payload: Dict[str, Any] = Depends(verify_token)):
    """Обновить сообщение"""
    message = messages_db.get(message_id)
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Проверяем, что сообщение принадлежит сессии пользователя
    session = sessions_db.get(message.get("session_id"))
    if not session or session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Проверяем, что это сообщение пользователя (не ответ ассистента)
    if message.get("role") != "user":
        raise HTTPException(status_code=400, detail="Only user messages can be edited")
    
    message["content"] = request.content
    message["updated_at"] = datetime.now().isoformat()
    
    return message


@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: str, payload: Dict[str, Any] = Depends(verify_token)):
    """Удалить сообщение и все последующие"""
    message = messages_db.get(message_id)
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Проверяем, что сообщение принадлежит сессии пользователя
    session = sessions_db.get(message.get("session_id"))
    if not session or session.get("user_id") != payload.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Находим все сообщения в сессии и сортируем по времени
    session_messages = []
    for msg_id, msg in messages_db.items():
        if msg.get("session_id") == message.get("session_id"):
            session_messages.append(msg)
    
    session_messages.sort(key=lambda x: x.get("created_at", ""))
    
    # Находим индекс удаляемого сообщения
    delete_index = -1
    for i, msg in enumerate(session_messages):
        if msg["id"] == message_id:
            delete_index = i
            break
    
    # Удаляем это сообщение и все последующие
    messages_to_delete = []
    for i, msg in enumerate(session_messages):
        if i >= delete_index:
            messages_to_delete.append(msg["id"])
    
    for msg_id in messages_to_delete:
        if msg_id in messages_db:
            del messages_db[msg_id]
    
    return {"success": True}


def generate_bot_response(user_message: str) -> str:
    """Генерация ответа от бота (заглушка, в реальном приложении здесь будет вызов LLM)"""
    import random
    
    responses = [
        f"Я понял ваш вопрос о '{user_message[:20]}...' и подумаю над ним.",
        f"Спасибо за сообщение: '{user_message[:30]}...'. Это интересная тема!",
        f"Я получил ваше сообщение и анализирую его содержание.",
        f"Отличный вопрос! Давайте рассмотрим '{user_message[:25]}...' подробнее.",
        f"Благодарю вас за информацию. Вот что я могу сказать по теме: '{user_message[:20]}...'"
    ]
    
    return random.choice(responses)


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