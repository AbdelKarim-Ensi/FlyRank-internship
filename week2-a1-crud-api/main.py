from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A small in-memory CRUD API for a to-do list (FlyRank Internship, W2 A1).",
)

# In-memory "database": gone when the server stops
tasks = [
    {"id": 1, "title": "Learn HTTP", "done": True},
    {"id": 2, "title": "Build a CRUD API", "done": False},
    {"id": 3, "title": "Push to GitHub", "done": False},
]


# --- OpenAPI documentation helpers (Swagger UI) ---
def error_response(status_code: int, description: str, example: str):
    return {
        status_code: {
            "description": description,
            "content": {"application/json": {"example": {"error": example}}},
        }
    }


NOT_FOUND = error_response(404, "Task not found", "Task 99 not found")
BAD_REQUEST = error_response(
    400, "Invalid body", "'title' is required and must be a non-empty string"
)


def json_body(properties: dict, example: dict, required: list | None = None):
    # The body is read manually with Request, so we describe it for Swagger by hand
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return {
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": schema, "example": example}},
        }
    }


CREATE_BODY = json_body(
    properties={"title": {"type": "string"}},
    example={"title": "Buy milk"},
    required=["title"],
)
UPDATE_BODY = json_body(
    properties={"title": {"type": "string"}, "done": {"type": "boolean"}},
    example={"title": "Buy oat milk", "done": True},
)


# --- Helpers ---
def error(status_code: int, message: str):
    return JSONResponse(status_code=status_code, content={"error": message})


def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


# --- Endpoints ---
@app.get("/", summary="API info", description="Describes the API and its endpoints.")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Health check", description="Returns ok if the server is alive.")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List tasks", description="Returns all tasks.")
def list_tasks():
    return tasks


@app.get(
    "/tasks/{task_id}",
    summary="Get one task",
    description="Returns the task with the given id, or 404 if it does not exist.",
    responses={**NOT_FOUND},
)
def get_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a task from a JSON body. 'title' is required and non-empty. "
    "The server sets the id and done=false.",
    responses={**BAD_REQUEST},
    openapi_extra=CREATE_BODY,
)
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


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Updates 'title' and/or 'done'. At least one is required. "
    "Unknown id gives 404, invalid body gives 400.",
    responses={**BAD_REQUEST, **NOT_FOUND},
    openapi_extra=UPDATE_BODY,
)
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


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Deletes the task. Returns 204 with an empty body, or 404 if unknown.",
    responses={**NOT_FOUND},
)
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return error(404, f"Task {task_id} not found")
    tasks.remove(task)
    return Response(status_code=204)
