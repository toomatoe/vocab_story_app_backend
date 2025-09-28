import os
from typing import Dict
import hashlib

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment once at module level
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate API key efficiently
PLACEHOLDER_VALUES = frozenset({
    "your_google_api_key_here",
    "your_api_key_here", 
    "AIza-placeholder",
    "placeholder",
    "xxx",
    "fake_key"
})

USE_MOCK_MODE = (
    not API_KEY or 
    not API_KEY.strip() or 
    API_KEY.strip().lower() in PLACEHOLDER_VALUES
)

# Configure API once if valid
if not USE_MOCK_MODE:
    genai.configure(api_key=API_KEY)

MOCK_STORY_TEMPLATE = (
    "This is a mock story for the word '{word}'. The story generation is currently running in mock mode "
    "because the GOOGLE_API_KEY is not configured. Please set the API key in your .env file to get real stories."
)

# Pre-define length configurations to avoid recreation
LENGTH_CONFIGS = {
    "brief": {
        "template": "Create a very short story about '{}' in just 1-2 paragraphs (100-150 words). Keep it educational and appropriate for children.",
        "tokens": 200
    },
    "short": {
        "template": "Create a short story about '{}' (200-300 words) that demonstrates its meaning. Keep it educational and appropriate for children.",
        "tokens": 400
    },
    "medium": {
        "template": "Create a medium-length story about '{}' (400-500 words) with rich details that clearly shows its meaning. Keep it educational and appropriate for children.",
        "tokens": 650
    },
    "long": {
        "template": "Create a detailed, engaging story about '{}' (600-800 words) with character development and a clear plot that demonstrates the word's meaning. Keep it educational and appropriate for children.",
        "tokens": 1000
    }
}

# Initialize model once at module level
_model = None
if not USE_MOCK_MODE:
    _model = genai.GenerativeModel('gemini-2.0-flash')

class StoryGenerationError(Exception):
    pass


def _get_cache_key(word: str, story_length: str, temperature: float, max_tokens: int) -> str:
    """Generate efficient cache key"""
    return hashlib.md5(
        f"{word}_{story_length}_{temperature}_{max_tokens}".encode()
    ).hexdigest()


def _manage_cache_size():
    """Simple cache eviction - remove oldest 20% of entries if limit exceeded"""
    if len(_story_cache) > _cache_size_limit:
        # Remove oldest 20% of entries (simple FIFO)
        keys_to_remove = list(_story_cache.keys())[:_cache_size_limit // 5]
        for key in keys_to_remove:
            del _story_cache[key]


def get_mock_mode() -> bool:
    """Efficient getter for mock mode status"""
    return USE_MOCK_MODE


def clear_cache() -> int:
    """Clear story cache and return number of items cleared"""
    count = len(_story_cache)
    _story_cache.clear()
    return count


# Simple in-memory cache for stories (in production, use Redis/Memcached)
_story_cache: Dict[str, str] = {}
_cache_size_limit = 100

def _get_cache_key(word: str, story_length: str, temperature: float, max_tokens: int) -> str:
    """Generate efficient cache key"""
    return hashlib.md5(
        f"{word}_{story_length}_{temperature}_{max_tokens}".encode()
    ).hexdigest()

def _manage_cache_size():
    """Simple cache eviction - remove oldest entries if limit exceeded"""
    if len(_story_cache) > _cache_size_limit:
        # Remove oldest 20% of entries (simple FIFO)
        keys_to_remove = list(_story_cache.keys())[:_cache_size_limit // 5]
        for key in keys_to_remove:
            del _story_cache[key]

async def generate_story(word: str, *, temperature: float = 0.7, max_tokens: int = 500, story_length: str = "short") -> str:
    # Input validation
    if not word or not word.strip():
        raise ValueError("'word' must be a non-empty string")
    
    word = word.strip().lower()  # Normalize for caching

    if USE_MOCK_MODE:
        return MOCK_STORY_TEMPLATE.format(word=word)

    # Get configuration (no dictionary recreation)
    config = LENGTH_CONFIGS.get(story_length, LENGTH_CONFIGS["short"])
    adjusted_max_tokens = min(max_tokens, config["tokens"])
    
    # Check cache first
    cache_key = _get_cache_key(word, story_length, temperature, adjusted_max_tokens)
    if cache_key in _story_cache:
        return _story_cache[cache_key]

    # Generate prompt efficiently using template
    prompt = config["template"].format(word)

    try:
        # Use pre-initialized model
        response = _model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=adjusted_max_tokens,
            )
        )
    except Exception as e:
        raise StoryGenerationError(f"Google Gemini API request failed: {e}") from e

    # Validate response efficiently
    if not response.candidates or not response.candidates[0].content.parts:
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        if finish_reason == 2:  # SAFETY
            raise StoryGenerationError("Story generation was blocked by safety filters. Try a different word.")
        elif finish_reason == 3:  # RECITATION
            raise StoryGenerationError("Story generation was blocked due to recitation concerns. Try a different word.")
        else:
            raise StoryGenerationError(f"Story generation failed with finish reason: {finish_reason}")

    # Extract and validate content
    content = response.candidates[0].content.parts[0].text
    if not content or not content.strip():
        raise StoryGenerationError("Empty content returned from Google Gemini API")

    result = content.strip()
    
    # Cache the result
    _story_cache[cache_key] = result
    _manage_cache_size()  # Keep cache size manageable
    
    return result
