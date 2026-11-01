import os
from uuid import uuid4

import httpx
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

app = FastAPI(title="Watchlist Service")

MOVIE_SERVICE_URL = os.getenv(
    "MOVIE_SERVICE_URL",
    "http://localhost:8000",
)

templates = Jinja2Templates(directory="templates")

watchlists: dict[str, dict] = {}


class WatchlistCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WatchlistMovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    year: int | None = Field(default=None, ge=1888, le=2100)


def find_watchlist(watchlist_id: str) -> dict:
    watchlist = watchlists.get(watchlist_id)
    if watchlist is None:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


@app.get("/health")
def health():
    return {"status": "ok", "service": "watchlist-service"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{MOVIE_SERVICE_URL}/movies")
        movies = response.json() if response.status_code == 200 else []

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"movies": movies},
    )

@app.post("/add-movie", response_class=HTMLResponse)
async def add_movie_form(
    request: Request,
    title: str = Form(...),
    year: int | None = Form(default=None),
):
    payload = {"title": title}
    if year is not None:
        payload["year"] = year

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{MOVIE_SERVICE_URL}/movies",
            json=payload,
        )

        if response.status_code != 201:
            raise HTTPException(
                status_code=502,
                detail="Movie Service unavailable",
            )

        movies_response = await client.get(f"{MOVIE_SERVICE_URL}/movies")

    if movies_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Could not load movies from Movie Service",
        )

    movies = movies_response.json()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"movies": movies},
    )


@app.post("/watchlists", status_code=201)
def create_watchlist(watchlist: WatchlistCreate):
    watchlist_id = str(uuid4())
    saved = {
        "id": watchlist_id,
        "name": watchlist.name,
        "movies": [],
    }
    watchlists[watchlist_id] = saved
    return saved


@app.get("/watchlists")
def list_watchlists():
    return list(watchlists.values())


@app.get("/watchlists/{watchlist_id}")
def get_watchlist(watchlist_id: str):
    return find_watchlist(watchlist_id)


@app.post("/watchlists/{watchlist_id}/movies", status_code=201)
async def add_movie_to_watchlist(
    watchlist_id: str,
    movie: WatchlistMovieCreate,
):
    watchlist = find_watchlist(watchlist_id)

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            f"{MOVIE_SERVICE_URL}/movies",
            json=movie.model_dump(),
        )

    if response.status_code != 201:
        raise HTTPException(
            status_code=response.status_code,
            detail="Could not add movie through Movie Service",
        )

    created_movie = response.json()
    watchlist["movies"].append(created_movie)
    return watchlist
