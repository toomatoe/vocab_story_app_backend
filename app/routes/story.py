from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.gemini_service import generate_story, StoryGenerationError, get_mock_mode, clear_cache, get_cache_stats

# Data models for API requests and responses
class StoryRequest(BaseModel):
    """Request model for story generation"""
    word: str = Field(..., min_length=1)  # The vocabulary word to build a story around
    length: str = Field(default="short", pattern="^(brief|short|medium|long)$")  # How long the story should be

class StoryResponse(BaseModel):
    """Response model containing the generated story"""
    word: str      # The original vocabulary word
    story: str     # The AI-generated story
    length: str    # The requested story length
    mock: bool     # Whether this was generated using mock mode

# API router for all story-related endpoints
router = APIRouter()

@router.post("/generate_story", response_model=StoryResponse)
async def create_story(request: StoryRequest):
    """Generate a story using AI based on a vocabulary word"""
    try:
        story_content = await generate_story(request.word, story_length=request.length)
        return StoryResponse(
            word=request.word,
            story=story_content,
            length=request.length,
            mock=get_mock_mode()
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except StoryGenerationError as error:
        raise HTTPException(status_code=502, detail=f"I couldn't generate a sigma story: {error}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Oopsie: {error}")

@router.delete("/cache")
async def clear_story_cache():
    """Clear all cached stories to free up memory"""
    cleared_count = clear_cache()
    return {"message": f"Cache cleared. Removed {cleared_count} cached stories."}

@router.get("/health")
async def get_system_status():
    """Check system health and get cache performance statistics"""
    return {
        "status": "healthy",
        "mock_mode": get_mock_mode(),
        "cache_enabled": True,
        "cache_stats": get_cache_stats()
    }

