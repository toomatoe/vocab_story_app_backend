# Vocabulary Story App Backend

Backend API for the vocab story Chrome extension. Generates educational fantasy stories to teach vocabulary words through context.

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── routes/
│   └── story.py         # Story generation endpoints
├── services/
│   └── openai_service.py # OpenAI integration and mock mode
├── models/              # Database models (future)
└── db/                  # Database configuration (future)
```

## API Documentation

### Endpoints

#### `POST /generate_story`
Generates a short fantasy story that teaches a vocabulary word through context.

**Request Body:**
```json
{
  "word": "luminous"
}
```

**Response:**
```json
{
  "word": "luminous",
  "story": "Generated story content...",
  "mock": false
}
```

**Response Fields:**
- `word` (string): The vocabulary word from the request
- `story` (string): Generated story content
- `mock` (boolean): `true` if using mock mode (no API key), `false` for real OpenAI stories

**Error Responses:**
- `400 Bad Request`: Invalid or missing word
- `502 Bad Gateway`: OpenAI service failure
- `500 Internal Server Error`: Unexpected server error

## Core Functions

### `generate_story(word, temperature=0.7, max_tokens=500)`
Located in `app/services/openai_service.py`

**Parameters:**
- `word` (str): Vocabulary word to embed in story
- `temperature` (float, optional): Creativity level (0.0-2.0, default 0.7)
- `max_tokens` (int, optional): Maximum story length (default 500)

**Returns:**
- `str`: Generated story text or mock placeholder

**Raises:**
- `ValueError`: Empty or invalid word
- `StoryGenerationError`: OpenAI API failures

### Mock Mode
Automatically activates when:
- `OPENAI_API_KEY` is missing from `.env`
- API key is empty or whitespace
- API key contains placeholder values like `"your_openai_api_key_here"`

## Setup & Installation

1. **Clone and navigate:**
   ```bash
   git clone <repo-url>
   cd vocab_story_app_backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   - Copy `.env.example` to `.env` (if exists)
   - Set `OPENAI_API_KEY=your_actual_api_key` in `.env`
   - Leave as placeholder for mock mode during development

5. **Run the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access API docs:**
   - Interactive docs: http://127.0.0.1:8000/docs
   - OpenAPI schema: http://127.0.0.1:8000/openapi.json

## Development Notes

- **Mock Mode**: Perfect for frontend development without OpenAI costs
- **Error Handling**: Comprehensive error responses for robust client integration
- **Pydantic Models**: Automatic request/response validation
- **Temperature Control**: Adjustable creativity for story generation
- **Auto-reload**: Server restarts automatically on code changes

## Future Enhancements

- Database integration for story caching
- User authentication and rate limiting
- Multiple story styles/themes
- Story difficulty levels
- Analytics and usage tracking

---

**KYCombinator Nov 2025**
