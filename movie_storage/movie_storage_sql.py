import requests
from sqlalchemy import create_engine, text
import config

# API and Database
DB_URL = "sqlite:///data/movies.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
api_key = config.OMDB_API_KEY
if not api_key:
    raise RuntimeError("Missing OMDB_API_KEY env var. Set it before running.")


def _init_db():
    """Generate users and movies tables if they don't exist."""
    with engine.connect() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                year INTEGER,
                rating REAL NOT NULL,
                poster_url TEXT,
                imdb_id TEXT,
                UNIQUE(user_id, title),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))

        connection.commit()

_init_db()


def _fetch_from_omdb(title: str) -> dict:
    """ Fetch Data from OMDb API and store in DB """
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

    api_title = data.get("Title", "").strip()
    year_str = str(data.get("Year", "")).strip()
    poster_url = data.get("Poster", None)
    imdb_rating = str(data.get("imdbRating") or "").strip()
    imdb_id = data.get("imdbID")

    if not api_title or not year_str:
        raise ValueError("OMDb returned incomplete data")

    year = int(year_str[:4])
    rating = float(imdb_rating) if imdb_rating and imdb_rating != "N/A" else 0.0

    if poster_url == "N/A":
        poster_url = None

    return {
        "title": api_title,
        "year": year,
        "rating": rating,
        "poster_url": poster_url,
        "imdb_id": imdb_id
    }


def list_users():
    """Return all users as a list of dicts."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id, name FROM users ORDER BY name ASC")
        ).fetchall()

    return [{"id": r[0], "name": r[1]} for r in rows]


def create_user(name: str) -> int:
    """Create a new user (or return existing user id)."""
    name = name.strip()
    if not name:
        raise ValueError("User name cannot be empty.")

    with engine.connect() as connection:
        # Try insert (ignore if already exists)
        connection.execute(
            text("INSERT OR IGNORE INTO users (name) VALUES (:name)"),
            {"name": name}
        )
        connection.commit()

        # Fetch id
        user_id = connection.execute(
            text("SELECT id FROM users WHERE name = :name"),
            {"name": name}
        ).scalar_one()

    return user_id


def list_movies(user_id: int):
    """Return all movies for a specific user as a dict keyed by title."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT title, year, rating, poster_url, imdb_id
                FROM movies
                WHERE user_id = :user_id
                ORDER BY title ASC
            """),
            {"user_id": user_id}
        ).fetchall()

    return {
        title: {
            "year": year,
            "rating": rating,
            "poster_url": poster_url,
            "imdb_id": imdb_id,
        }
        for title, year, rating, poster_url, imdb_id in rows
    }


def add_movie(user_id, title):
    info = _fetch_from_omdb(title)

    with engine.connect() as connection:
        try:
            connection.execute(
                text("""
                    INSERT INTO movies (user_id, title, year, rating, poster_url, imdb_id)
                    VALUES (:user_id, :title, :year, :rating, :poster_url, :imdb_id)
                """),
                {
                    "user_id": user_id,
                    "title": info["title"],
                    "year": info["year"],
                    "rating": info["rating"],
                    "poster_url": info["poster_url"],
                    "imdb_id": info["imdb_id"],
                }
            )
            connection.commit()
            print(f"Movie '{info['title']}' added successfully.")
        except Exception:
            print(f"Movie '{info['title']}' already exists for this user.")


def delete_movie(user_id, title):
    with engine.connect() as connection:
        result = connection.execute(
            text("DELETE FROM movies WHERE user_id = :uid AND title = :title"),
            {"uid": user_id, "title": title}
        )
        connection.commit()

    if result.rowcount == 0:
        print(f"Movie '{title}' not found for this user.")
    else:
        print(f"Movie '{title}' deleted successfully.")


def update_movie(user_id, title, year, rating):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                UPDATE movies
                SET year = :year, rating = :rating
                WHERE user_id = :uid AND title = :title
            """),
            {"uid": user_id, "title": title, "year": year, "rating": rating}
        )
        connection.commit()

    if result.rowcount == 0:
        print(f"Movie '{title}' not found for this user.")
    else:
        print(f"Movie '{title}' updated successfully.")