# AI Todo Assistant API

A FastAPI backend project that combines a Todo CRUD API with an LLM-powered task extraction assistant.

Users can create todos manually, or describe tasks in natural language and let the AI extract tasks, due times, and save them into the SQLite database.

## Features

- FastAPI backend
- Todo CRUD API
- SQLite persistence with SQLModel
- Request and response validation with Pydantic
- HTTP status codes and error handling
- Swagger UI API documentation
- Docker support
- Docker volume support for persistent SQLite data
- Bailian / DashScope LLM integration
- AI chat endpoint
- Natural language task extraction
- AI-generated todos with due time extraction

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLModel
- SQLite
- Uvicorn
- Docker
- OpenAI-compatible SDK
- Alibaba Cloud Bailian / DashScope

## Project Structure

```text
fastapi-todo-api/
├── data/
│   └── todos.db
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── main.py
├── README.md
└── requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen3.5-plus
```

Do not commit `.env` to GitHub.

Use `.env.example` as the public template.

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## Run with Docker

Build the Docker image:

```bash
docker build -t fastapi-todo-api .
```

Run the container:

```bash
docker run -p 8000:8000 fastapi-todo-api
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

If port `8000` is already in use:

```bash
docker run -p 8001:8000 fastapi-todo-api
```

Then open:

```text
http://127.0.0.1:8001/docs
```

## Run with Docker and Persistent SQLite Data

Create a local data directory:

```bash
mkdir data
```

Build the image:

```bash
docker build -t fastapi-todo-api .
```

Run with a volume:

```bash
docker run -p 8001:8000 -v "${PWD}/data:/app/data" fastapi-todo-api
```

For Windows PowerShell:

```powershell
$projectPath = (Get-Location).Path
docker run -p 8001:8000 -v "${projectPath}\data:/app/data" fastapi-todo-api
```

The SQLite database will be stored in:

```text
data/todos.db
```

## API Endpoints

### Basic Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/about` | Project information |
| POST | `/echo` | Echo test endpoint |
| POST | `/chat` | Mock chat endpoint |

### Todo Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/todos` | List all todos |
| POST | `/todos` | Create a todo |
| GET | `/todos/{todo_id}` | Get a todo by id |
| PATCH | `/todos/{todo_id}` | Update a todo |
| DELETE | `/todos/{todo_id}` | Delete a todo |

### AI Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/ai/chat` | Chat with the LLM |
| POST | `/ai/extract-tasks` | Extract todo tasks from natural language |
| POST | `/ai/create-todos` | Extract tasks and save them into the database |

## Todo API Examples

### Create a Todo

Request:

```json
{
  "title": "Learn FastAPI",
  "due_time": "Tomorrow morning"
}
```

Response:

```json
{
  "id": 1,
  "title": "Learn FastAPI",
  "completed": false,
  "due_time": "Tomorrow morning"
}
```

### List Todos

Request:

```text
GET /todos
```

Response:

```json
[
  {
    "id": 1,
    "title": "Learn FastAPI",
    "completed": false,
    "due_time": "Tomorrow morning"
  }
]
```

### Update a Todo

Request:

```json
{
  "title": "Review FastAPI",
  "completed": true,
  "due_time": "Tonight"
}
```

Response:

```json
{
  "id": 1,
  "title": "Review FastAPI",
  "completed": true,
  "due_time": "Tonight"
}
```

### Delete a Todo

Request:

```text
DELETE /todos/1
```

Response:

```json
{
  "message": "Todo deleted"
}
```

## AI API Examples

### AI Chat

Endpoint:

```text
POST /ai/chat
```

Request:

```json
{
  "message": "用一句话鼓励我继续学习 FastAPI"
}
```

Response:

```json
{
  "user_message": "用一句话鼓励我继续学习 FastAPI",
  "assistant_message": "继续加油，掌握 FastAPI 会让你具备构建现代 Web 服务的核心能力。",
  "model": "qwen3.5-plus"
}
```

### Extract Tasks from Natural Language

Endpoint:

```text
POST /ai/extract-tasks
```

Request:

```json
{
  "text": "明天上午九点学习 FastAPI，下午三点写 Docker 总结，晚上复习 SQLModel"
}
```

Response:

```json
{
  "tasks": [
    {
      "title": "学习 FastAPI",
      "time": "明天上午九点"
    },
    {
      "title": "写 Docker 总结",
      "time": "明天下午三点"
    },
    {
      "title": "复习 SQLModel",
      "time": "明天晚上"
    }
  ]
}
```

### Create Todos with AI

Endpoint:

```text
POST /ai/create-todos
```

Request:

```json
{
  "text": "明天上午九点学习 FastAPI，下午三点写 Docker 总结，晚上复习 SQLModel"
}
```

Response:

```json
{
  "extracted_tasks": [
    {
      "title": "学习 FastAPI",
      "time": "明天上午九点"
    },
    {
      "title": "写 Docker 总结",
      "time": "明天下午三点"
    },
    {
      "title": "复习 SQLModel",
      "time": "明天晚上"
    }
  ],
  "created_todos": [
    {
      "id": 1,
      "title": "学习 FastAPI",
      "completed": false,
      "due_time": "明天上午九点"
    },
    {
      "id": 2,
      "title": "写 Docker 总结",
      "completed": false,
      "due_time": "明天下午三点"
    },
    {
      "id": 3,
      "title": "复习 SQLModel",
      "completed": false,
      "due_time": "明天晚上"
    }
  ]
}
```

## Current Version

`v0.9` - AI Todo Assistant backend with Docker, SQLite persistence, and LLM-powered task creation.

## What I Learned

- How to build a FastAPI backend
- How to design RESTful CRUD endpoints
- How to use Pydantic request and response models
- How to use path parameters and request bodies
- How to handle HTTP errors
- How to use SQLModel with SQLite
- How to persist data with a database
- How to Dockerize a FastAPI project
- How to use Docker volumes for persistent data
- How to call an OpenAI-compatible LLM API
- How to extract structured JSON from natural language
- How to connect AI output with backend business logic

## Next Steps

- Add filtering by completed status
- Add filtering by due time
- Add better time parsing
- Add tests with pytest
- Add logging and configuration cleanup
- Add a simple frontend
- Deploy the API online