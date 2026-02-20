import pickle
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

POSTGRES_CONN = os.getenv("POSTGRES_CONN", "").replace("@postgres:", "@localhost:")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "movie_similarity.pkl")


def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def get_db_connection():
    return psycopg2.connect(POSTGRES_CONN)


def fetch_movies_by_ids(movie_ids):
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            movie_id,
            title,
            year,
            rating,
            runtime,
            summary,
            director,
            actors,
            poster,
            genres,
            trailer
        FROM movie_details
        WHERE movie_id = ANY(%s)
    """

    cur.execute(query, (movie_ids,))
    rows = cur.fetchall()
    conn.close()

    movies = []

    for row in rows:
        movies.append({
            "movie_id": row[0],
            "title": row[1],
            "year": row[2],
            "rating": row[3],
            "runtime": row[4],
            "summary": row[5],
            "director": row[6],
            "actors": ", ".join(row[7]) if row[7] else "",
            "poster_url": row[8],
            "tags": ", ".join(row[9]) if row[9] else "",
            "trailer_url": row[10] if row[10] else ""
        })

    return movies
