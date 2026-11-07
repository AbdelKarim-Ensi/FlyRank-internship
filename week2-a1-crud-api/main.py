from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

# In-memory "database": gone when the server stops
tasks = [
    {"id": 1, "title": "Learn HTTP", "done": True},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Push to GitHub", "done": False},
]


def error(status_code: int, message: str):
    return JSONResponse(status_code=status_code, content={"error": message})


def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    return task


@app.post("/tasks", status_code=201)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return error(400, "Request body must be valid JSON")

    if not isinstance(body, dict):
        return error(400, "Request body must be a JSON object")

    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        return error(400, "'title' is required and must be a non-empty string")

    next_id = max((t["id"] for t in tasks), default=0) + 1
    task = {"id": next_id, "title": title.strip(), "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}")
async def update_task(task_id: int, request: Request):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")

    try:
        body = await request.json()
    except Exception:
        return error(400, "Request body must be valid JSON")

    if not isinstance(body, dict):
        return error(400, "Request body must be a JSON object")

    if "title" not in body and "done" not in body:
        return error(400, "Provide at least 'title' or 'done'")

    if "title" in body:
        title = body["title"]
        if not isinstance(title, str) or not title.strip():
            return error(400, "'title' must be a non-empty string")
    if "done" in body and not isinstance(body["done"], bool):
        return error(400, "'done' must be true or false")

    # Validation passed: apply changes
    if "title" in body:
        task["title"] = body["title"].strip()
    if "done" in body:
        task["done"] = body["done"]
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    tasks.remove(task)
    return Response(status_code=204)
