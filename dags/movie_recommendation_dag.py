from pydoc import describe
from airflow.decorators import dag, task
from airflow.utils.timezone import datetime
import psycopg2
import os
import pickle
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger_eng')
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
import re

POSTGRES_CONN = os.getenv("POSTGRES_CONN")
MODEL_PATH = "/opt/airflow/models/movie_similarity.pkl"


@dag(
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["movies", "ml", "recommendation"]
)
def movie_recommendation_dag():

    @task
    def fetch_movies():
        conn = psycopg2.connect(POSTGRES_CONN)
        query = "SELECT movie_id, title, summary, genres, director, actors FROM movie_details WHERE summary IS NOT NULL"
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    @task
    def preprocess_text(df: pd.DataFrame):
        # Move downloads here so they don't slow down the Airflow UI
        nltk.download('stopwords'); nltk.download('punkt'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger_eng')
        
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words("english"))

        def get_wordnet_pos(word):
            tag = nltk.pos_tag([word])[0][1][0].upper()
            tag_dict = {"J": wordnet.ADJ, "N": wordnet.NOUN, "V": wordnet.VERB, "R": wordnet.ADV}
            return tag_dict.get(tag, wordnet.NOUN)

        def clean_and_lemmatize(text):
            text = text.lower()
            text = re.sub(r"[^a-zA-Z ]", "", text)
            tokens = [t for t in text.split() if t not in stop_words]
            return " ".join([lemmatizer.lemmatize(w, get_wordnet_pos(w)) for w in tokens])

        df["summary_clean"] = df["summary"].fillna("").apply(clean_and_lemmatize)
        df["genres_text"] = df["genres"].apply(lambda x: " ".join(x) if isinstance(x, np.ndarray) and x.size > 0 else "")
        df["actors_text"] = df["actors"].apply(lambda x: " ".join(x) if isinstance(x, np.ndarray) and x.size > 0 else "")
        df["director_text"] = df["director"].fillna("")

        file_path = "/opt/airflow/data/processed_movies.parquet"
        df[["movie_id", "title", "summary_clean", "genres_text", "actors_text", "director_text"]].to_parquet(file_path)
        return file_path 

    @task
    def vectorize_and_weight(file_path):
        df = pd.read_parquet(file_path)
        
        # Vectorization logic...
        summary_vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        actors_vec = TfidfVectorizer(max_features=3000); director_vec = TfidfVectorizer(max_features=1000); genres_vec = TfidfVectorizer(max_features=2000)

        combined_features = np.hstack([
            0.4 * summary_vec.fit_transform(df["summary_clean"]).toarray(),
            0.2 * actors_vec.fit_transform(df["actors_text"]).toarray(),
            0.1 * director_vec.fit_transform(df["director_text"]).toarray(),
            0.3 * genres_vec.fit_transform(df["genres_text"]).toarray()
        ])

        # FIX: Save NumPy array to disk to avoid XCom error
        feature_path = "/opt/airflow/data/features.npy"
        np.save(feature_path, combined_features)

        return {"movie_ids": df["movie_id"].tolist(), "titles": df["title"].tolist(), "feature_path": feature_path}

    @task
    def reduce_and_compute_similarity(data):
        features = np.load(data["feature_path"]) # Load from disk
        svd = TruncatedSVD(n_components=200, random_state=42)
        reduced_features = svd.fit_transform(features)
        
        # FIX: We save the artifact as a path because the matrix is too big for XCom
        model_artifact = {
            "movie_ids": data["movie_ids"], 
            "titles": data["titles"], 
            "svd": svd, 
            "similarity_matrix": cosine_similarity(reduced_features)
        }
        
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model_artifact, f)
            
        return MODEL_PATH

    # Pipeline execution
    df = fetch_movies()
    processed_path = preprocess_text(df)
    features_data = vectorize_and_weight(processed_path)
    final_model_path = reduce_and_compute_similarity(features_data)
    
movie_recommendation_dag()
