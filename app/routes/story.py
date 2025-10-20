from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.gemini_service import generate_story, StoryGenerationError, get_mock_mode, clear_cache, get_cache_stats

# Request/response models define the API contract for story generation
class StoryGenerationRequest(BaseModel):
    vocabulary_word: str = Field(..., min_length=1)
    story_length: str = Field(default="short", pattern="^(brief|short|medium|long)$")
    word_meaning_context: str = Field(default="", description="Optional context to specify which meaning of the word to use")

class GeneratedStoryResponse(BaseModel):
    vocabulary_word: str
    generated_story: str
    requested_length: str
    provided_context: str
    is_mock_response: bool

# Router handles all story-related API endpoints
story_router = APIRouter()

@story_router.post("/generate_story", response_model=GeneratedStoryResponse)
async def create_vocabulary_story(story_request: StoryGenerationRequest):
    # Main endpoint that uses AI to generate educational stories from vocabulary words
    try:
        # Call Gemini AI service to create story content
        ai_generated_content = await generate_story(
            story_request.vocabulary_word, 
            story_length=story_request.story_length, 
            context=story_request.word_meaning_context
        )
        
        # Package the generated story with metadata for the response
        return GeneratedStoryResponse(
            vocabulary_word=story_request.vocabulary_word,
            generated_story=ai_generated_content,
            requested_length=story_request.story_length,
            provided_context=story_request.word_meaning_context,
            is_mock_response=get_mock_mode()
        )
    
    # Convert service errors into appropriate HTTP responses
    except ValueError as validation_error:
        raise HTTPException(status_code=400, detail=str(validation_error))
    except StoryGenerationError as generation_error:
        raise HTTPException(status_code=502, detail=f"Failed to generate story: {generation_error}")
    except Exception as unexpected_error:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {unexpected_error}")

@story_router.delete("/cache")
async def clear_all_cached_stories():
    # Admin endpoint to clear cached stories and free up memory
    number_of_stories_cleared = clear_cache()
    return {"message": f"Cache cleared. Removed {number_of_stories_cleared} cached stories."}

@story_router.get("/health")
async def get_application_health_status():
    # Health check endpoint that reports system status and performance metrics
    current_cache_statistics = get_cache_stats()
    return {
        "status": "healthy",
        "mock_mode": get_mock_mode(),
        "cache_enabled": True,
        "cache_stats": current_cache_statistics
    }

