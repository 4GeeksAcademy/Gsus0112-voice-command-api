from fastapi import APIRouter, HTTPException, status
from typing import List

from src.app.schemas.voice import Task, TaskCreate, TaskReplace, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

tasks_db: List[dict] = []
current_id = 1


@router.get("", response_model=list[Task])
def get_tasks() -> list[Task]:
    return tasks_db


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    global current_id
    new_task = {
        "id": current_id,
        "title": payload.title,
        "done": payload.done
    }
    current_id += 1
    tasks_db.append(new_task)
    return new_task


@router.put("/{task_id}", response_model=Task)
def replace_task(
    task_id: int,
    payload: TaskReplace,
) -> Task:
    for task in tasks_db:
        if task["id"] == task_id:
            task["title"] = payload.title
            task["done"] = payload.done
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@router.patch("/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    payload: TaskUpdate,
) -> Task:
    for task in tasks_db:
        if task["id"] == task_id:
            if payload.title is not None:
                task["title"] = payload.title
            if payload.done is not None:
                task["done"] = payload.done
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@router.delete("/{task_id}")
def delete_task(task_id: int) -> dict[str, str]:
    for i, task in enumerate(tasks_db):
        if task["id"] == task_id:
            del tasks_db[i]
            return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")