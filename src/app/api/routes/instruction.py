import json
from fastapi import APIRouter, HTTPException, status
from groq import Groq

from src.app.schemas.voice import InstructionPayload, InstructionRequest
from src.app.core.config import get_settings

router = APIRouter(tags=["instruction"])

SYSTEM_PROMPT = """You are an AI assistant that translates natural language voice commands into API actions for a task list app.
Your response MUST be ONLY a raw JSON object and nothing else. No markdown formatting, no backticks, no explanations.

The available endpoints are:
- GET /tasks : list tasks
- POST /tasks : create a task (requires 'title' in params)
- PUT /tasks/<task_id> : replace a task (requires 'title' and 'done' in params)
- PATCH /tasks/<task_id> : update a task (requires 'title' and/or 'done' in params)
- DELETE /tasks/<task_id> : delete a task

Extract the user's intent and output JSON in this exact format:
{
  "endpoint": "/tasks" or "/tasks/<id>",
  "method": "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
  "params": { ... }
}

Example: "añade comprar leche a mi lista"
Output:
{
  "endpoint": "/tasks",
  "method": "POST",
  "params": { "title": "comprar leche" }
}

Example: "marca la tarea 3 como completada"
Output:
{
  "endpoint": "/tasks/3",
  "method": "PATCH",
  "params": { "done": true }
}

Example: "borra la tarea 5"
Output:
{
  "endpoint": "/tasks/5",
  "method": "DELETE",
  "params": {}
}

If the user wants to list tasks:
{
  "endpoint": "/tasks",
  "method": "GET",
  "params": {}
}
"""

@router.post("/instruction", response_model=InstructionPayload)
def route_instruction(
    payload: InstructionRequest,
) -> InstructionPayload:
    settings = get_settings()
    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload.transcription},
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        parsed_content = json.loads(content)
        return InstructionPayload(**parsed_content)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process instruction: {str(e)}",
        )