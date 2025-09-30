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
_cache_eviction_threshold = 120  # Only check when we exceed this

# Pre-compile regex for word validation
_word_pattern = re.compile(r'^[a-zA-Z\s\-\']+$')

def _get_cache_key(word: str, story_length: str, temperature: float, max_tokens: int) -> str:
    """Generate efficient cache key - simple string concatenation is faster than MD5 for short keys"""
    return f"{word}_{story_length}_{temperature}_{max_tokens}"

def _evict_cache_if_needed():
    """Only evict cache when we exceed threshold - more efficient"""
    if len(_story_cache) > _cache_eviction_threshold:
        # Remove oldest entries to get back to limit
        while len(_story_cache) > _cache_size_limit:
            _story_cache.popitem(last=False)  # Remove oldest (FIFO)load_dotenv

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

# Initialize model once at module level with optimal configuration
_model = None
_generation_config_cache = {}

if not USE_MOCK_MODE:
    _model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Pre-create common generation configs to avoid recreation
    _generation_config_cache = {
        (0.7, 200): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=200),
        (0.7, 400): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=400), 
        (0.7, 650): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=650),
        (0.7, 1000): genai.types.GenerationConfig(temperature=0.7, max_output_tokens=1000),
    }

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


def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics for monitoring"""
    return {
        "cache_size": len(_story_cache),
        "cache_limit": _cache_size_limit,
        "eviction_threshold": _cache_eviction_threshold,
        "cache_usage_percent": int((len(_story_cache) / _cache_size_limit) * 100)
    }


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
    """
    Optimized story generation with efficient caching and validation
    """
    # Fast input validation and normalization
    if not word:
        raise ValueError("'word' must be a non-empty string")
    
    # Single pass normalization - strip and lowercase together
    normalized_word = word.strip().lower()
    if not normalized_word:
        raise ValueError("'word' must contain valid characters")
    
    # Validate word contains only valid characters (cached regex)
    if not _word_pattern.match(normalized_word):
        raise ValueError("'word' must contain only letters, spaces, hyphens, and apostrophes")

    if USE_MOCK_MODE:
        return MOCK_STORY_TEMPLATE.format(word=normalized_word)

    # Fast config lookup with cached defaults
    config = LENGTH_CONFIGS.get(story_length, LENGTH_CONFIGS["short"])
    adjusted_max_tokens = min(max_tokens, config["tokens"])
    
    # Optimized cache key (simple string concat is faster than MD5 for short keys)
    cache_key = _get_cache_key(normalized_word, story_length, temperature, adjusted_max_tokens)
    
    # Check cache with OrderedDict - moves to end for LRU behavior
    if cache_key in _story_cache:
        # Move to end (most recently used)
        _story_cache.move_to_end(cache_key)
        return _story_cache[cache_key]

    # Generate prompt efficiently using template
    prompt = config["template"].format(normalized_word)

    try:
        # Use cached generation config if available, otherwise create new one
        config_key = (temperature, adjusted_max_tokens)
        generation_config = _generation_config_cache.get(
            config_key,
            genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=adjusted_max_tokens,
            )
        )
        
        # Use pre-initialized model with optimized config
        response = _model.generate_content(prompt, generation_config=generation_config)
    except Exception as e:
        raise StoryGenerationError(f"Google Gemini API request failed: {e}") from e

    # Optimized response validation with safe attribute access
    try:
        candidate = response.candidates[0]
        content_parts = candidate.content.parts
        
        if not content_parts:
            # Handle safety filter blocks efficiently
            finish_reason = getattr(candidate, 'finish_reason', None)
            if finish_reason == 2:  # SAFETY
                raise StoryGenerationError("Story generation was blocked by safety filters. Try a different word.")
            elif finish_reason == 3:  # RECITATION
                raise StoryGenerationError("Story generation was blocked due to recitation concerns. Try a different word.")
            else:
                raise StoryGenerationError(f"Story generation failed with finish reason: {finish_reason}")
        
        # Extract content efficiently
        content = content_parts[0].text
        if not content:
            raise StoryGenerationError("Empty content returned from Google Gemini API")
        
        # Single strip operation
        result = content.strip()
        if not result:
            raise StoryGenerationError("Only whitespace content returned from Google Gemini API")
        
    except (IndexError, AttributeError) as e:
        raise StoryGenerationError(f"Invalid response structure from Google Gemini API: {e}") from e
    
    # Cache the result with efficient eviction
    _story_cache[cache_key] = result
    _evict_cache_if_needed()  # Only evict when threshold exceeded
    
    return result
