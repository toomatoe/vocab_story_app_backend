import os
from typing import Dict
import hashlib
from collections import OrderedDict
import re

import google.generativeai as genai
from dotenv import load_dotenv

# Optimized cache with better performance
_story_cache: OrderedDict[str, str] = OrderedDict()
_cache_size_limit = 100
_cache_eviction_threshold = 120

# Pre-compile regex for word validation
_word_pattern = re.compile(r'^[a-zA-Z\s\-\']+$')

def _evict_cache_if_needed():
    """Only evict cache when we exceed threshold - more efficient"""
    if len(_story_cache) > _cache_eviction_threshold:
        while len(_story_cache) > _cache_size_limit:
            _story_cache.popitem(last=False)

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

PLACEHOLDER_VALUES = frozenset({
    "your_google_api_key_here", "your_api_key_here", "AIza-placeholder", 
    "placeholder", "xxx", "fake_key"
})

USE_MOCK_MODE = (
    not API_KEY or not API_KEY.strip() or 
    API_KEY.strip().lower() in PLACEHOLDER_VALUES
)

if not USE_MOCK_MODE:
    genai.configure(api_key=API_KEY)

MOCK_STORY_TEMPLATE = (
    "This is a mock story for the word '{word}'. The story generation is currently "
    "running in mock mode because the GOOGLE_API_KEY is not configured."
)

LENGTH_CONFIGS = {
    "brief": {
        "template": "Create a very short story about '{}' in 1-2 paragraphs (100-150 words).",
        "tokens": 200
    },
    "short": {
        "template": "Create a short story about '{}' (200-300 words) that demonstrates its meaning.",
        "tokens": 400
    },
    "medium": {
        "template": "Create a medium-length story about '{}' (400-500 words) with rich details.",
        "tokens": 650
    },
    "long": {
        "template": "Create a detailed story about '{}' (600-800 words) with character development.",
        "tokens": 1000
    }
}

_model = None
_generation_config_cache = {}

if not USE_MOCK_MODE:
    _model = genai.GenerativeModel('gemini-2.0-flash')
    _generation_config_cache = {
        (0.7, 200): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=200),
        (0.7, 400): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=400), 
        (0.7, 650): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=650),
        (0.7, 1000): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=1000),
    }

class StoryGenerationError(Exception):
    pass


def _get_cache_key(word: str, story_length: str, temperature: float, max_tokens: int) -> str:
    """Generate efficient cache key using simple string concatenation"""
    return f"{word}_{story_length}_{temperature}_{max_tokens}"

def get_mock_mode() -> bool:
    """Get mock mode status"""
    return USE_MOCK_MODE

def clear_cache() -> int:
    """Clear story cache and return number of items cleared"""
    count = len(_story_cache)
    _story_cache.clear()
    return count

def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics for monitoring"""
    return {
        "cache_size": len(_story_cache),
        "cache_limit": _cache_size_limit,
        "eviction_threshold": _cache_eviction_threshold,
        "cache_usage_percent": int((len(_story_cache) / _cache_size_limit) * 100)
    }

async def generate_story(word: str, *, temperature: float = 0.7, max_tokens: int = 500, story_length: str = "short") -> str:
    """Optimized story generation with efficient caching and validation"""
    if not word:
        raise ValueError("'word' must be a non-empty string")
    
    normalized_word = word.strip().lower()
    if not normalized_word:
        raise ValueError("'word' must contain valid characters")
    
    if not _word_pattern.match(normalized_word):
        raise ValueError("'word' must contain only letters, spaces, hyphens, and apostrophes")

    if USE_MOCK_MODE:
        return MOCK_STORY_TEMPLATE.format(word=normalized_word)

    config = LENGTH_CONFIGS.get(story_length, LENGTH_CONFIGS["short"])
    adjusted_max_tokens = min(max_tokens, config["tokens"])
    
    cache_key = _get_cache_key(normalized_word, story_length, temperature, adjusted_max_tokens)
    
    if cache_key in _story_cache:
        _story_cache.move_to_end(cache_key)
        return _story_cache[cache_key]

    prompt = config["template"].format(normalized_word)

    try:
        config_key = (temperature, adjusted_max_tokens)
        generation_config = _generation_config_cache.get(
            config_key,
            genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=adjusted_max_tokens,
            )
        )
        
        response = _model.generate_content(prompt, generation_config=generation_config)
    except Exception as e:
        raise StoryGenerationError(f"Google Gemini API request failed: {e}") from e

    try:
        candidate = response.candidates[0]
        content_parts = candidate.content.parts
        
        if not content_parts:
            finish_reason = getattr(candidate, 'finish_reason', None)
            if finish_reason == 2:
                raise StoryGenerationError("Story generation was blocked by safety filters. Try a different word.")
            elif finish_reason == 3:
                raise StoryGenerationError("Story generation was blocked due to recitation concerns. Try a different word.")
            else:
                raise StoryGenerationError(f"Story generation failed with finish reason: {finish_reason}")
        
        content = content_parts[0].text
        if not content:
            raise StoryGenerationError("Empty content returned from Google Gemini API")
        
        result = content.strip()
        if not result:
            raise StoryGenerationError("Only whitespace content returned from Google Gemini API")
        
    except (IndexError, AttributeError) as e:
        raise StoryGenerationError(f"Invalid response structure from Google Gemini API: {e}") from e
    
    _story_cache[cache_key] = result
    _evict_cache_if_needed()
    
    return result
