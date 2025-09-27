import os
from typing import Optional

import openai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

PLACEHOLDER_VALUES = {
    "your_openai_api_key_here",
    "your_api_key_here", 
    "sk-placeholder",
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
    "because the OPENAI_API_KEY is not configured. Please set the API key in your .env file to get real stories."
)



class StoryGenerationError(Exception):
    pass


async def generate_story(word: str, *, temperature: float = 0.7, max_tokens: int = 500) -> str:
    if not word or not word.strip():
        raise ValueError("'word' must be a non-empty string")

    if USE_MOCK_MODE:
        return MOCK_STORY_TEMPLATE.format(word=word)

    prompt = (
        "You are a helpful creative writing assistant. "
        "Write a concise (<= 350 words) whimsical fantasy micro-story that teaches the meaning of the vocabulary word '"
        f"{word}' through context. The story should: \n"
        "- Imply the definition via events rather than stating it outright.\n"
        "- Use age-appropriate, clear language.\n"
        "- End with a single sentence moral or hint that reinforces the word's meaning.\n"
        "Do not define the word explicitly.\n"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise StoryGenerationError(f"OpenAI API request failed: {e}") from e

    try:
        content: Optional[str] = response.choices[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise StoryGenerationError("Unexpected response format from OpenAI API") from e

    if not content:
        raise StoryGenerationError("Empty content returned from OpenAI API")

    return content.strip()
