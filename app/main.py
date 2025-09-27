from fastapi import FastAPI
from app.routes import story

app =  FastAPI()
app.include_router(story.router)