from datetime import timedelta
from airflow.decorators import dag, task
import pendulum
import psycopg2
import os

POSTGRES_CONN = os.getenv("POSTGRES_CONN")
BATCH_SIZE = 20  # number of movies processed per DAG run


@dag(
    schedule="*/2 * * * *",   # can change later
    start_date=pendulum.now("UTC").subtract(days=1),
    dagrun_timeout=timedelta(minutes=40),
    max_active_runs=1,
    catchup=False,
    tags=["movies", "transform"]
)
def movie_transformation_dag():

    @task
    def fetch_unprocessed_movies():
        conn = psycopg2.connect(POSTGRES_CONN)
        cur = conn.cursor()

        cur.execute("""
            SELECT movie_id, payload
            FROM raw_movie_api
            WHERE processed_at IS NULL
            ORDER BY fetched_at
            LIMIT %s
        """, (BATCH_SIZE,))

        rows = cur.fetchall()
        conn.close()

        return rows

    @task
    def transform_and_load(rows):
        if not rows:
            return "No new movies to process"

        conn = psycopg2.connect(POSTGRES_CONN)
        cur = conn.cursor()

        for movie_id, payload in rows:
            genres = [g["name"] for g in payload.get("genres", [])]

            cast = payload.get("credits", {}).get("cast", [])[:5]
            crew = payload.get("credits", {}).get("crew", [])

            director = next(
                (c["name"] for c in crew if c.get("job") == "Director"),
                None
            )

            actors = [c["name"] for c in cast]

            trailer_key = next(
                (
                    v["key"]
                    for v in payload.get("videos", {}).get("results", [])
                    if v.get("site") == "YouTube" and v.get("type") == "Trailer"
                ),
                None
            )

            trailer_url = (
                f"https://www.youtube.com/watch?v={trailer_key}"
                if trailer_key else None
            )

            poster_url = (
                f"https://image.tmdb.org/t/p/w500{payload.get('poster_path')}"
                if payload.get("poster_path") else None
            )

            cur.execute("""
                INSERT INTO movie_details (
                    movie_id, title, summary, year, runtime,
                    rating, rating_count, genres,
                    director, actors, trailer, poster
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (movie_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    runtime = EXCLUDED.runtime,
                    rating = EXCLUDED.rating,
                    rating_count = EXCLUDED.rating_count,
                    genres = EXCLUDED.genres,
                    director = EXCLUDED.director,
                    actors = EXCLUDED.actors,
                    trailer = EXCLUDED.trailer,
                    poster = EXCLUDED.poster,
                    last_updated = NOW();
            """, (
                movie_id,
                payload.get("title"),
                payload.get("overview"),
                int(payload.get("release_date", "0000")[:4]),
                payload.get("runtime"),
                payload.get("vote_average"),
                payload.get("vote_count"),
                genres,
                director,
                actors,
                trailer_url,
                poster_url
            ))

            cur.execute("""
                UPDATE raw_movie_api
                SET processed_at = NOW()
                WHERE movie_id = %s
            """, (movie_id,))

        conn.commit()
        conn.close()

        return f"Processed {len(rows)} movies"

    rows = fetch_unprocessed_movies()
    transform_and_load(rows)


movie_transformation_dag()
