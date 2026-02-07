import movie_storage.movie_storage_sql as storage
import random
import matplotlib.pyplot as plt
import os
import config

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
CYAN = "\033[36m"

ACTIVE_USER_ID = None
ACTIVE_USER_NAME = None

def select_user():
    users = storage.list_users()

    print("\nWelcome to Movie Hub!\n")
    if users:
        print("Select a user:")
        for i, u in enumerate(users, start=1):
            print(f" {i}. {u['name']}")
        print(f" {len(users) + 1}. Create new user\n")

        choice = input("Enter choice: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(users):
                u = users[idx - 1]
                return u["id"], u["name"]
            if idx == len(users) + 1:
                name = input("Enter new user name: ").strip()
                uid = storage.create_user(name)
                return uid, name

    name = input("No users found. Create your first user name: ").strip()
    uid = storage.create_user(name)
    return uid, name

def show_menu():
    """Display the main menu with available user actions."""
    print(
        f"{CYAN}Menu:\n"
        " 0.  Exit\n"
        " 1.  List movies\n"
        " 2.  Add movie\n"
        " 3.  Delete movie\n"
        " 4.  Update movie\n"
        " 5.  View stats\n"
        " 6.  Random movie\n"
        " 7.  Search movie\n"
        " 8.  Movies sorted by rating\n"
        " 9.  Create rating Histogram\n"
        " 10. Movies sorted by year\n"
        " 11. Filter movies\n"
        " 12. Generate website\n"
        " 13. Switch user\n"
        f"{RESET}"
    )

def exit_app():
  raise SystemExit


def list_movies():
    """Print all movies in the database along with their ratings and year."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{ACTIVE_USER_NAME}, your movie collection is empty.")
        return

    print(f"\n{len(movies)} movies in total:\n")
    for title, info in movies.items():
        print(f"{title}: {info['rating']} ({info['year']})")


def add_movie():
    title = input(f"{GREEN}Enter movie title: {RESET}").strip()
    if not title:
        print(f"{RED}Title cannot be empty.{RESET}")
        return

    try:
        storage.add_movie(ACTIVE_USER_ID, title)
    except ValueError as e:
        print(f"{RED}Movie not found: {e}{RESET}")
    except ConnectionError as e:
        print(f"{RED}OMDb not accessible: {e}{RESET}")
    except RuntimeError as e:
        print(f"{RED}{e}{RESET}")


def delete_movie():
    """Delete an existing movie from the database."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies to delete.{RESET}")
        return

    title = input(f"{GREEN}Enter movie name to delete: {RESET}").strip()
    if not title:
        print(f"{RED}Movie title cannot be empty.{RESET}")
        return

    if title in movies:
        storage.delete_movie(ACTIVE_USER_ID, title)
        print(f"{title} has been deleted.")
    else:
        print(f"{RED}Error: Movie does not exist.{RESET}")


def update_movie():
    """Update the rating and year of an existing movie with validation."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies to update.{RESET}")
        return

    title = input(f"{GREEN}Enter movie name to update: {RESET}").strip()
    if not title:
        print(f"{RED}Movie title cannot be empty.{RESET}")
        return

    if title not in movies:
        print(f"{RED}Error: Movie does not exist.{RESET}")
        return

    while True:
        try:
            rating_input = input(f"{GREEN}Enter new movie rating (0-10): {RESET}").strip()
            rating = float(rating_input)
            if 0 <= rating <= 10:
                break
            else:
                print(f"{RED}Rating must be between 0 and 10.{RESET}")
        except ValueError:
            print(f"{RED}Invalid rating. Please enter a number between 0 and 10.{RESET}")

    while True:
        try:
            year_input = input(f"{GREEN}Enter new movie year: {RESET}").strip()
            year = int(year_input)
            break
        except ValueError:
            print(f"{RED}Invalid year. Please enter a valid number.{RESET}")

    storage.update_movie(ACTIVE_USER_ID, title, year, rating)
    print(f"Movie '{title}' successfully updated to rating {rating} ({year}).")


def show_stats():
    """Calculate and display statistics about movie ratings."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies in the database.{RESET}")
        return

    ratings = [info["rating"] for info in movies.values()]
    ratings.sort()

    avg = sum(ratings) / len(ratings)
    mid = len(ratings) // 2
    median = ratings[mid] if len(ratings) % 2 else (ratings[mid - 1] + ratings[mid]) / 2

    max_rating = max(ratings)
    min_rating = min(ratings)

    print(f"Average rating: {avg:.1f}")
    print(f"Median rating: {median:.1f}")

    for title, info in movies.items():
        if info["rating"] == max_rating:
            print(f"Best movie: {title}, {info['rating']:.1f} ({info['year']})")
        if info["rating"] == min_rating:
            print(f"Worst movie: {title}, {info['rating']:.1f} ({info['year']})")


def random_movie():
    """Select and display a random movie from the database."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies in the database.{RESET}")
        return

    title, info = random.choice(list(movies.items()))
    print(f"Your movie for tonight: {title}, rated {info['rating']} ({info['year']})")


def search_movie():
    """Search for movies containing a user-provided search term."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    term = input(f"{GREEN}Enter part of movie name: {RESET}").lower()
    if not term:
        print(f"{RED}Search term cannot be empty.{RESET}")
        return

    found = False
    for title, info in movies.items():
        if term in title.lower():
            print(f"{title}, {info['rating']} ({info['year']})")
            found = True

    if not found:
        print(f"{RED}No movies found matching '{term}'.{RESET}")


def sort_movies_by_rating():
    """Display movies sorted by rating in descending order."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies in the database.{RESET}")
        return

    for title, info in sorted(movies.items(), key=lambda x: x[1]["rating"], reverse=True):
        print(f"{title}, {info['rating']} ({info['year']})")


def create_histogram():
    """Create and save a histogram of movie ratings."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies in the database.{RESET}")
        return

    filename = input(f"{GREEN}Enter filename (e.g. ratings.png): {RESET}")
    ratings = [info["rating"] for info in movies.values()]

    plt.hist(ratings, bins=10, edgecolor="black")
    plt.title("Movie Ratings Histogram")
    plt.xlabel("Rating")
    plt.ylabel("Number of Movies")
    plt.savefig(filename)
    plt.close()

    print(f"Histogram saved as '{filename}'")


def sort_movies_by_year():
    """Display movies sorted by year."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies in the database.{RESET}")
        return

    while True:
        order = input(f"{GREEN}Do you want to see the latest movies first? (y/n): {RESET}").strip().lower()
        if order in ("y", "n"):
            break
        else:
            print(f"{RED}Invalid input. Please enter 'y' or 'n'.{RESET}")

    reverse = True if order == "y" else False

    sorted_movies = sorted(movies.items(), key=lambda x: x[1]["year"], reverse=reverse)

    for title, info in sorted_movies:
        print(f"{title}, {info['rating']} ({info['year']})")


def filter_movies():
    """Filter movies based on minimum rating, start year, and end year."""
    movies = storage.list_movies(ACTIVE_USER_ID)
    if not movies:
        print(f"{RED}No movies in the database.{RESET}")
        return

    while True:
        min_rating_input = input(f"{GREEN}Enter minimum rating (leave blank for no minimum rating): {RESET}").strip()
        if not min_rating_input:
            min_rating = None
            break
        try:
            min_rating = float(min_rating_input)
            if 0 <= min_rating <= 10:
                break
            else:
                print(f"{RED}Rating must be between 0 and 10.{RESET}")
        except ValueError:
            print(f"{RED}Invalid rating. Please enter a number between 0 and 10.{RESET}")

    while True:
        start_year_input = input(f"{GREEN}Enter start year (leave blank for no start year): {RESET}").strip()
        if not start_year_input:
            start_year = None
            break
        try:
            start_year = int(start_year_input)
            break
        except ValueError:
            print(f"{RED}Invalid year. Please enter a valid number.{RESET}")

    while True:
        end_year_input = input(f"{GREEN}Enter end year (leave blank for no end year): {RESET}").strip()
        if not end_year_input:
            end_year = None
            break
        try:
            end_year = int(end_year_input)
            break
        except ValueError:
            print(f"{RED}Invalid year. Please enter a valid number.{RESET}")

    filtered = []
    for title, info in movies.items():
        rating_ok = min_rating is None or info["rating"] >= min_rating
        start_ok = start_year is None or info["year"] >= start_year
        end_ok = end_year is None or info["year"] <= end_year
        if rating_ok and start_ok and end_ok:
            filtered.append((title, info["year"], info["rating"]))

    if filtered:
        print(f"\nFiltered Movies:")
        for title, year, rating in filtered:
            print(f"{title} ({year}): {rating}")
    else:
        print(f"{RED}No movies match the criteria.{RESET}")


def generate_website():
  """Generate a user-specific HTML page from _static/index_template.html."""
  movies = storage.list_movies(ACTIVE_USER_ID)

  base_dir = os.path.dirname(os.path.abspath(__file__))
  static_dir = os.path.join(base_dir, "_static")

  template_path = os.path.join(static_dir, "index_template.html")
  safe_name = ACTIVE_USER_NAME.strip().replace(" ", "_")
  output_path = os.path.join(static_dir, f"{safe_name}.html")

  try:
    with open(template_path, "r", encoding="utf-8") as f:
      template = f.read()
  except FileNotFoundError:
    print(f"{RED}Error: _static/index_template.html not found.{RESET}")
    return

  movie_items = []

  for title, info in movies.items():
      year = info.get("year", "")
      poster_url = info.get("poster_url") or ""

      movie_items.append(
          "        <li>\n"
          '            <div class="movie">\n'
          f'                <img class="movie-poster" src="{poster_url}"/>\n'
          f'                <div class="movie-title">{title}</div>\n'
          f'                <div class="movie-year">{year}</div>\n'
          "            </div>\n"
          "        </li>\n"
      )

  movie_grid_html = "".join(movie_items)

  html = template.replace(
      "__TEMPLATE_TITLE__",
      f"{ACTIVE_USER_NAME}'s {config.APP_TITLE}"
  )
  html = html.replace("__TEMPLATE_MOVIE_GRID__", movie_grid_html)

  with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

  print(f"Website was generated successfully: {safe_name}.html")


def switch_user():
    global ACTIVE_USER_ID, ACTIVE_USER_NAME
    ACTIVE_USER_ID, ACTIVE_USER_NAME = select_user()
    print(f"\nActive user: {ACTIVE_USER_NAME}\n")


def main():
    """Run the movie database application."""
    print("\n********** My Movie Database **********")

    global ACTIVE_USER_ID, ACTIVE_USER_NAME
    ACTIVE_USER_ID, ACTIVE_USER_NAME = select_user()
    print(f"\nActive user: {ACTIVE_USER_NAME}\n")

    actions = {
        "0": exit_app,
        "1": list_movies,
        "2": add_movie,
        "3": delete_movie,
        "4": update_movie,
        "5": show_stats,
        "6": random_movie,
        "7": search_movie,
        "8": sort_movies_by_rating,
        "9": create_histogram,
        "10": sort_movies_by_year,
        "11": filter_movies,
        "12": generate_website,
        "13": switch_user
    }

    while True:
        show_menu()
        choice = input(f"{GREEN}Enter choice (0-13): {RESET}").strip()

        if choice == "0":
          raise SystemExit

        elif choice in actions:
            actions[choice]()
            input(f"{GREEN}\nPress enter to return to menu {RESET}")
        else:
            print(f"{RED}Invalid choice.{RESET}")


if __name__ == "__main__":
    main()