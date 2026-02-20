def recommend_movies(title, model_artifact, fetch_movies_by_ids, top_n=10):
    title_lower = title.lower()

    titles = [t.lower() for t in model_artifact["titles"]]
    movie_ids = model_artifact["movie_ids"]
    similarity = model_artifact["similarity_matrix"]

    if title_lower not in titles:
        return []

    idx = titles.index(title_lower)

    scores = list(enumerate(similarity[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    recommended_ids = [
        movie_ids[i]
        for i, _ in scores[1: top_n + 1]
    ]

    # Fetch full metadata from Postgres
    return fetch_movies_by_ids(recommended_ids)
