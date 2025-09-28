import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY and API_KEY.strip():
    genai.configure(api_key=API_KEY)

PLACEHOLDER_VALUES = {
    "your_google_api_key_here",
    "your_api_key_here", 
    "AIza-placeholder",
    "placeholder",
    "xxx",
    "fake_key"
}

USE_MOCK_MODE = (
    not API_KEY or 
    not API_KEY.strip() or 
    API_KEY.strip().lower() in PLACEHOLDER_VALUES
)

MOCK_STORY_TEMPLATE = (
    "This is a mock story for the word '{word}'. The story generation is currently running in mock mode "
    "because the GOOGLE_API_KEY is not configured. Please set the API key in your .env file to get real stories."
)


class StoryGenerationError(Exception):
    pass


async def generate_story(word: str, *, temperature: float = 0.7, max_tokens: int = 500, story_length: str = "short") -> str:
    if not word or not word.strip():
        raise ValueError("'word' must be a non-empty string")

    if USE_MOCK_MODE:
        return MOCK_STORY_TEMPLATE.format(word=word)

    length_configs = {
        "brief": {
            "prompt": f"Create a very short story about '{word}' in just 1-2 paragraphs (100-150 words). Keep it educational and appropriate for children.",
            "tokens": 200
        },
        "short": {
            "prompt": f"Create a short story about '{word}' (200-300 words) that demonstrates its meaning. Keep it educational and appropriate for children.",
            "tokens": 400
        },
        "medium": {
            "prompt": f"Create a medium-length story about '{word}' (400-500 words) with rich details that clearly shows its meaning. Keep it educational and appropriate for children.",
            "tokens": 650
        },
        "long": {
            "prompt": f"Create a detailed, engaging story about '{word}' (600-800 words) with character development and a clear plot that demonstrates the word's meaning. Keep it educational and appropriate for children.",
            "tokens": 1000
        }
    }
    
    config = length_configs.get(story_length, length_configs["short"])
    prompt = config["prompt"]
    adjusted_max_tokens = min(max_tokens, config["tokens"])

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=adjusted_max_tokens,
            )
        )
    except Exception as e:
        raise StoryGenerationError(f"Google Gemini API request failed: {e}") from e

    # Check if response was blocked by safety filters
    if not response.candidates or not response.candidates[0].content.parts:
        if response.candidates and response.candidates[0].finish_reason:
            finish_reason = response.candidates[0].finish_reason
            if finish_reason == 2:  # SAFETY
                raise StoryGenerationError("Story generation was blocked by safety filters. Try a different word.")
            elif finish_reason == 3:  # RECITATION
                raise StoryGenerationError("Story generation was blocked due to recitation concerns. Try a different word.")
            else:
                raise StoryGenerationError(f"Story generation failed with finish reason: {finish_reason}")
        else:
            raise StoryGenerationError("No content was generated")

    # Extract text from the first part
    content = response.candidates[0].content.parts[0].text

    if not content or not content.strip():
        raise StoryGenerationError("Empty content returned from Google Gemini API")

    return content.strip()
