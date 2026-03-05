from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.dependencies import get_db

from .schemas import CopilotRequest, CopilotResponse
from .service import VoiceCopilotService

router = APIRouter(prefix="/voice", tags=["AI Voice Copilot"])

def get_voice_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> VoiceCopilotService:
    return VoiceCopilotService(db)

@router.post("/process-text", response_model=CopilotResponse)
async def process_voice_to_cart(request: CopilotRequest, service: VoiceCopilotService = Depends(get_voice_service)):
    """
    Takes a transcribed text string from the user's browser (e.g. "Do samosa aur ek chai dena"),
    sends it to the AI NLP engine (Gemini), matches it against the current menu, 
    and returns a structured JSON order update with a conversational reply and upsell recommendations.
    """
    if not request.transcript:
        raise HTTPException(status_code=400, detail="Transcript text is required")
        
    response = await service.process_voice_transcript(request)
    return response

@router.get("/health")
async def voice_copilot_health():
    """Simple endpoint to verify the voice copilot module is reachable."""
    return {"status": "ok", "message": "Voice Copilot API is ready to accept text transcripts."}
