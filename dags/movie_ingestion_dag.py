from datetime import timedelta
from airflow.decorators import dag, task
import pendulum
import psycopg2
import os
import requests
import json
import time
from airflow.exceptions import AirflowFailException

TMDB_API_KEY = None  # read inside task
BASE_URL = "https://api.themoviedb.org/3"


@dag(
    schedule="*/2 * * * *",  
    dagrun_timeout=timedelta(minutes=30),
    max_active_runs=1,
    start_date=pendulum.now("UTC").subtract(days=1),
    catchup=False, 
    tags=["movies", "ingestion"]
)
def movie_ingestion_dag():

    @task
    def get_current_page():
        
        conn = psycopg2.connect(os.getenv("POSTGRES_CONN"))
        cur = conn.cursor()

        cur.execute("""
            SELECT current_page
            FROM ingestion_state
            WHERE pipeline_name = 'tmdb_top_rated'
        """)
        page = cur.fetchone()[0]
        conn.close()

        return page

    @task
    def fetch_movie_ids(page):
        TMDB_API_KEY = os.getenv("TMDB_API_KEY")

        resp = requests.get(
            f"{BASE_URL}/movie/top_rated",
            params={"api_key": TMDB_API_KEY, "page": page},
            timeout=10
        )

        if resp.status_code != 200:
            raise AirflowFailException(f"TMDB error: {resp.text}")

        data = resp.json()
        results = data.get("results")

        if not results:
            raise AirflowFailException("No movies returned from TMDB")

        # Fetch all 20 movies from page
        return [m["id"] for m in results]

    @task
    def fetch_movie_payload(movie_ids):
        TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        movies = []

        for movie_id in movie_ids:
            resp = requests.get(
                f"{BASE_URL}/movie/{movie_id}",
                params={
                    "api_key": TMDB_API_KEY,
                    "append_to_response": "credits,videos"
                },
                timeout=10
            )

            if resp.status_code != 200:
                raise AirflowFailException(
                    f"Movie {movie_id} failed: {resp.text}"
                )

            movies.append({
                "movie_id": movie_id,
                "payload": resp.json()
            })

            time.sleep(0.3)  # ~3 req/sec → well under limit

        return movies

    @task
    def store_raw_payload(movies):
        conn = psycopg2.connect(os.getenv("POSTGRES_CONN"))
        cur = conn.cursor()

        for movie in movies:
            cur.execute("""
                INSERT INTO raw_movie_api (movie_id, payload)
                VALUES (%s, %s)
                ON CONFLICT (movie_id)
                DO UPDATE SET payload = EXCLUDED.payload,
                              fetched_at = NOW();
            """, (movie["movie_id"], json.dumps(movie["payload"])))

        conn.commit()
        conn.close()

    @task
    def update_page(page):
        next_page = page + 1 if page < 50 else 1

        conn = psycopg2.connect(os.getenv("POSTGRES_CONN"))
        cur = conn.cursor()

        cur.execute("""
            UPDATE ingestion_state
            SET current_page = %s,
                updated_at = NOW()
            WHERE pipeline_name = 'tmdb_top_rated'
        """, (next_page,))

        conn.commit()
        conn.close()

    page = get_current_page()
    ids = fetch_movie_ids(page)
    payloads = fetch_movie_payload(ids)
    store_raw_payload(payloads)
    update_page(page)


movie_ingestion_dag()
