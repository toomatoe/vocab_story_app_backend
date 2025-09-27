from fastapi import APIRouter, Request
from app.services.openai_service import generate_story

router = APIRouter()
@router.post("/generate_story")
async def story_endpoint(request: Request):
    data = await request.json()
    word = data["word"]
    story = await generate_story(word)
    return {"word": word, "story": story}

