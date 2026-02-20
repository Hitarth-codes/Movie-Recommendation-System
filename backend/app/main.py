from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from app.data_loader import load_model, fetch_movies_by_ids, get_db_connection
from app.recommender import recommend_movies
from app.schemas import RecommendationResponse

import psycopg2
import os
from dotenv import load_dotenv

from app.api_security import verify_api_key
from fastapi import Depends

from slowapi import Limiter
from slowapi.util import get_remote_address

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

POSTGRES_CONN = os.getenv("POSTGRES_CONN", "").replace("@postgres:", "@localhost:")

app = FastAPI(title="Movie Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model once
model = load_model()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# ---------------- SEARCH ----------------
@app.get("/search")
def search_movies(q: str = Query(..., min_length=1), api_key: str = Depends(verify_api_key)):
    conn = psycopg2.connect(POSTGRES_CONN)
    cur = conn.cursor()

    cur.execute("""
        SELECT title
        FROM movie_details
        WHERE LOWER(title) LIKE %s
        LIMIT 10
    """, (f"%{q.lower()}%",))

    results = [row[0] for row in cur.fetchall()]
    conn.close()

    return results


# ---------------- RECOMMEND ----------------
@app.get("/recommend", response_model=RecommendationResponse)
@limiter.limit("20/minute")
def recommend(request: Request, title: str, api_key: str = Depends(verify_api_key)):
    recs = recommend_movies(
        title,
        model,
        fetch_movies_by_ids
    )

    return {
        "selected_movie": title,
        "recommendations": recs
    }
