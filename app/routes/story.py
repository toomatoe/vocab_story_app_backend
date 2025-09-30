from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.openai_service import generate_story, StoryGenerationError, get_mock_mode, clear_cache, get_cache_stats

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
        story_content = await generate_story(payload.word, story_length=payload.length)
        return StoryResponse(
            word=payload.word,
            story=story_content,
            length=payload.length,
            mock=get_mock_mode()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StoryGenerationError as e:
        raise HTTPException(status_code=502, detail=f"Story generation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.delete("/cache")
async def clear_story_cache():
    """Clear the story cache and return number of items cleared"""
    cleared_count = clear_cache()
    return {"message": f"Cache cleared. Removed {cleared_count} cached stories."}


@router.get("/health")
async def health_check():
    """Health check endpoint with system status and cache stats"""
    cache_stats = get_cache_stats()
    return {
        "status": "healthy",
        "mock_mode": get_mock_mode(),
        "cache_enabled": True,
        "cache_stats": cache_stats
    }


@router.get("/cache/stats")
async def cache_statistics():
    """Get detailed cache performance statistics"""
    return get_cache_stats()

