import os
import requests
from sqlalchemy import create_engine, text
import config

# Database URL + key
DB_URL = "sqlite:///movies.db"
api_key = config.OMDB_API_KEY
if not api_key:
    raise RuntimeError("Missing OMDB_API_KEY env var. Set it before running.")

# Create the engine
engine = create_engine(DB_URL, echo=True)

# Create the movies db
def _init_db():
    with engine.connect() as connection:
        # Users table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """))

        # Movies table (user_id included)
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                year INTEGER NOT NULL,
                rating REAL NOT NULL,
                poster_url TEXT,
                UNIQUE(user_id, title),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))
        connection.commit()


# Fetch Data from OMDb API and store in DB
def _fetch_from_omdb(title: str) -> dict:
    api_key = config.OMDB_API_KEY
    if not api_key:
        raise RuntimeError("Missing OMDB_API_KEY env var. Set it before running.")

    url = "https://www.omdbapi.com/"
    params = {"t": title, "apikey": api_key}

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"OMDb connection error: {e}") from e

    if data.get("Response") != "True":
        raise ValueError(data.get("Error", "Movie not found"))

    # Parse fields
    api_title = data.get("Title", "").strip()
    year_str = str(data.get("Year", "")).strip()
    poster_url = data.get("Poster", None)
    imdb_rating_str = str(data.get("imdbRating", "")).strip()

    if not api_title or not year_str:
        raise ValueError("OMDb returned incomplete data")

    year = int(year_str[:4])
    rating = float(imdb_rating_str) if imdb_rating_str != "N/A" else 0.0

    if poster_url == "N/A":
        poster_url = None

    return {
        "title": api_title,
        "year": year,
        "rating": rating,
        "poster_url": poster_url
    }


def list_movies():
    """Retrieve all movies from the database."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT title, year, rating, poster_url FROM movies"))
        movies = result.fetchall()

    return {row[0]: {"year": row[1], "rating": row[2], "poster_url": row[3]} for row in movies}


def add_movie(title: str):
    """Add a movie by title (fetches year/rating/poster from OMDb)."""
    info = _fetch_from_omdb(title)  # may raise ValueError / ConnectionError

    with engine.connect() as connection:
        try:
            connection.execute(
                text("""
                    INSERT INTO movies (title, year, rating, poster_url)
                    VALUES (:title, :year, :rating, :poster_url)
                """),
                info
            )
            connection.commit()
            print(f"Movie '{info['title']}' added successfully.")
        except Exception as e:
            print(f"Error: {e}")


def delete_movie(title):
    """Delete a movie from the database."""
    with engine.connect() as connection:
        result = connection.execute(
            text("DELETE FROM movies WHERE title = :title"),
            {"title": title}
        )
        connection.commit()

        if result.rowcount == 0:
            print(f"Movie '{title}' not found.")
        else:
            print(f"Movie '{title}' deleted successfully.")


def update_movie(title, year, rating):
    """Update a movie's rating and year in the database."""
    with engine.connect() as connection:
        result = connection.execute(
            text("UPDATE movies SET rating = :rating, year = :year WHERE title = :title"),
            {"title": title, "year": year, "rating": rating}
        )
        connection.commit()

        if result.rowcount == 0:
            print(f"Movie '{title}' not found.")
        else:
            print(f"Movie '{title}' updated successfully.")