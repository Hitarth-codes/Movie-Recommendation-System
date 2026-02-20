from pydantic import BaseModel
from typing import List

class MovieCard(BaseModel):
    movie_id: int
    title: str
    year: int
    rating: float
    runtime: int
    summary: str
    director: str
    actors: str
    poster_url: str
    tags: str
    trailer_url: str

class RecommendationResponse(BaseModel):
    selected_movie: str
    recommendations: List[MovieCard]
