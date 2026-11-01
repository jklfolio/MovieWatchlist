import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient

app = FastAPI(title="Movie Service")

mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
mongo_client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
movies_collection = mongo_client["movie_watchlist"]["movies"]

class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    year: int | None = Field(default=None, ge=1888, le=2100)
    watched: bool = False

def serialize_movie(movie):
    movie["id"] = str(movie.pop("_id"))
    return movie

@app.get("/health")
def health():
    try:
        mongo_client.admin.command("ping")
        return {"status": "ok", "service": "movie-service", "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

@app.post("/movies", status_code=201)
def add_movie(movie: MovieCreate):
    saved = movie.model_dump()
    saved["_id"] = str(uuid4())
    movies_collection.insert_one(saved)
    return serialize_movie(saved)

@app.get("/movies")
def list_movies():
    return [serialize_movie(movie) for movie in movies_collection.find()]

@app.patch("/movies/{movie_id}/watched")
def mark_watched(movie_id: str):
    result = movies_collection.update_one(
        {"_id": movie_id},
        {"$set": {"watched": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Movie not found")
    return serialize_movie(movies_collection.find_one({"_id": movie_id}))
