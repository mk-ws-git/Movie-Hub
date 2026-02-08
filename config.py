import os

# Application
APP_TITLE = "movie hub"

# Database
DB_FILENAME = "movies.sqlite3"

# OMDb API
OMDB_API_URL = "https://www.omdbapi.com/"
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")

# Paths
STATIC_DIR = "_static"
TEMPLATE_FILE = "index_template.html"
OUTPUT_HTML = "index.html"