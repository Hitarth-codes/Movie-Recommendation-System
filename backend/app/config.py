from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MOVIES_CSV = DATA_DIR / "movies_db.csv"
SIMILARITY_PKL = DATA_DIR / "movies_similarity.pkl"
