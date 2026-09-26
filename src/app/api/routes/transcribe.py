from fastapi import APIRouter, HTTPException, UploadFile, File, status
from groq import Groq

from src.app.schemas.voice import TranscribeFlowResponse, InstructionRequest
from src.app.core.config import get_settings
from src.app.api.routes.instruction import route_instruction
from src.app.api.routes.tasks import get_tasks, create_task, replace_task, update_task, delete_task
from src.app.schemas.voice import TaskCreate, TaskReplace, TaskUpdate

router = APIRouter(tags=["transcribe"])

@router.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

@router.post("/transcribe", response_model=TranscribeFlowResponse)
async def transcribe_and_run_flow(file: UploadFile = File(...)) -> TranscribeFlowResponse:
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key)
    
    # 1. Transcribir el audio usando Whisper en Groq
    try:
        file_bytes = await file.read()
        # El modelo whisper-large-v3-turbo es super rápido
        transcription_response = client.audio.transcriptions.create(
            file=(file.filename or "audio.webm", file_bytes),
            model=settings.groq_transcription_model
        )
        transcription_text = transcription_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en transcripción: {str(e)}")

    if not transcription_text.strip():
        raise HTTPException(status_code=400, detail="No se pudo reconocer ningún texto.")

    # 2. Reutilizar nuestra lógica de /instruction para saber qué hacer
    instruction_req = InstructionRequest(transcription=transcription_text)
    instruction_payload = route_instruction(instruction_req)

    # 3. Ejecutar la acción localmente según lo que decidió el LLM
    endpoint = instruction_payload.endpoint
    method = instruction_payload.method
    params = instruction_payload.params
    result = None

    try:
        if method == "GET" and endpoint == "/tasks":
            result = get_tasks()
        elif method == "POST" and endpoint == "/tasks":
            result = create_task(TaskCreate(**params))
        else:
            # Extraer el ID numérico de la ruta (ej. /tasks/1)
            parts = endpoint.rstrip('/').split('/')
            task_id = int(parts[-1])

            if method == "PUT":
                result = replace_task(task_id, TaskReplace(**params))
            elif method == "PATCH":
                result = update_task(task_id, TaskUpdate(**params))
            elif method == "DELETE":
                result = delete_task(task_id)
            else:
                raise ValueError("Método no soportado")
    except Exception as e:
        result = {"error": str(e)}

    # 4. Devolver todo el flujo al frontend para que lo muestre
    return TranscribeFlowResponse(
        transcription=transcription_text,
        instruction=instruction_payload,
        result=result
    )