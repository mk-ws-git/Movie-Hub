import os

# Application
APP_TITLE = "Movie Hub"

# Database
DB_FILENAME = "movies.sqlite3"

# OMDb API
OMDB_API_URL = "https://www.omdbapi.com/"
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "cc1c26c3")

# Paths
STATIC_DIR = "_static"
TEMPLATE_FILE = "index_template.html"
OUTPUT_HTML = "index.html"