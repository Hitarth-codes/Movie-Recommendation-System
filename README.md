# Movie-Recommendation-System
Built a movie recommendation system using item-based collaborative filtering. Developed a similarity matrix for the top 250 IMDb movies based on tags, summaries, cast, and directors. The system provides movie recommendations by calculating movie similarities, improving user experience and discovery.

# Movie Recommendation System

## Overview
This project is a movie recommendation system that uses item-based collaborative filtering. The system recommends movies similar to a selected movie from the top 250 rated movies on IMDb. The recommendations are based on features such as tags, summary, cast, and directors.

## Features
- **Scraping IMDb Data**: Collected data for the top 250 rated movies on IMDb, including:
  - Movie name
  - Year
  - Runtime
  - Censorship
  - Ratings
  - Rating count
  - Tags
  - Summary
  - Director
  - Actors
- **Preprocessing**:
  - Removed stopwords and lemmatized the movie summaries.
  - Converted textual data (tags, summary, cast, and directors) into numerical form using the TF-IDF vectorizer.
- **Dimensionality Reduction**:
  - Applied Truncated SVD to reduce the dimensions of the data for efficiency.
- **Weighted Features**:
  - Assigned higher weights to tags and summaries to prioritize them in recommendations.
  - Assigned lower weights to actors and directors.
- **Similarity Matrix**:
  - Developed a similarity matrix using cosine similarity.
  - Calculated similarities between movies based on the processed data.
- **Movie Recommendations**:
  - Provides 10 recommendations for a user-selected movie.

## How It Works
1. **Input**: The user selects a movie they liked from the top 250 IMDb movies.
2. **Processing**:
   - Textual data of the selected movie is compared with other movies using the similarity matrix.
   - Higher priority is given to tags and summaries during comparison.
3. **Output**: The system returns a list of 10 recommended movies based on the similarity scores.

## Technologies Used
- **Python Libraries**:
  - BeautifulSoup and Selenium: For web scraping IMDb data.
  - NLTK: For text preprocessing (stopword removal and lemmatization).
  - Scikit-learn: For TF-IDF vectorization, Truncated SVD, and cosine similarity.
  - Pandas and NumPy: For data handling and processing.
- **Framework**: Python for development.


## Example
**Input**: "The Shawshank Redemption"

**Output**: 10 movies similar to "The Shawshank Redemption" based on tags, summary, cast, and directors.

## Future Enhancements
- Add support for user ratings and reviews to improve recommendations.
- Expand the dataset to include more movies from IMDb.
- Integrate a graphical user interface (GUI) for a better user experience.


