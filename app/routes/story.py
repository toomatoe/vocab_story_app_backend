from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.openai_service import generate_story, StoryGenerationError, USE_MOCK_MODE

class StoryRequest(BaseModel):
    word: str = Field(..., min_length=1)
    length: str = Field(default="short", pattern="^(brief|short|medium|long)$")

class StoryResponse(BaseModel):
    word: str
    story: str
    length: str
    mock: bool

router = APIRouter()

@router.post("/generate_story", response_model=StoryResponse)
async def story_endpoint(payload: StoryRequest):
    try:
        story_content = await generate_story(payload.word, payload.length)
        return StoryResponse(
            word=payload.word,
            story=story_content,
            length=payload.length,
            mock=USE_MOCK_MODE
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StoryGenerationError as e:
        raise HTTPException(status_code=502, detail=f"Story generation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

