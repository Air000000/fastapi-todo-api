from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="FastAPI Todo API")


class EchoRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200)
    repeat: int = Field(1, ge=1, le=5)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}


@app.get("/health")
def check_health():
    return {
        "status": "ok",
        "time": datetime.now().isoformat()
    }


@app.get("/about")
def about():
    return {
        "name": "fastapi-todo-api",
        "version": "0.1.0",
        "description": "My first FastAPI backend project"
    }


@app.post("/echo")
def echo(request: EchoRequest):
    return {
        "you_said": request.message,
        "repeat": request.repeat,
        "result": [request.message] * request.repeat
    }


@app.post("/chat")
def chat(request: ChatRequest):
    fake_response = f"这是一个模拟 AI 回复：我收到了你的消息「{request.message}」"

    return {
        "user_message": request.message,
        "assistant_message": fake_response
    }