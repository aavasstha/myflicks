# routes.py

from flask import (
    Blueprint, render_template, redirect, session, flash,
    request, url_for
)
import os
import requests
from flask_bcrypt import Bcrypt
from models import db, User, UserList, Movie
from forms import (
    SignupForm, LoginForm, SearchForm, AddListForm,
    UserListForm, RenameListForm
)

# Create the blueprint instance
main = Blueprint("main", __name__)
bcrypt = Bcrypt()

# Get TMDB token from environment
TMDB_BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN")

####################################
# Helper Functions
####################################

def get_popular_movies():
    """Fetch popular movies from the TMDB API."""
    url = "https://api.themoviedb.org/3/movie/popular?language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_BEARER_TOKEN
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        extracted_data = [
            {
                'id': result['id'],
                'title': result['title'],
                'overview': result['overview'],
                'poster_path': f"https://image.tmdb.org/t/p/w500{result['poster_path']}"
            }
            for result in data.get("results", [])
        ]
        return extracted_data
    else:
        flash("Something went wrong while fetching popular movies.")
        return []


def create_tmdb_token():
    """Request a new TMDB access token."""
    url = "https://api.themoviedb.org/3/authentication/token/new"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_BEARER_TOKEN
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("request_token")
    else:
        flash("Failed to retrieve access token")
        access_token = None
    return access_token


def find_movie(title):
    """Search for a movie by title via the TMDB API."""
    url = f"https://api.themoviedb.org/3/search/movie?query={title}&include_adult=false&language=en-US&page=1"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_BEARER_TOKEN
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        movie_data = [
            {
                'id': result['id'],
                'title': result['title'],
                'overview': result['overview'],
                'poster_path': f"https://image.tmdb.org/t/p/w500{result['poster_path']}"
            }
            for result in data.get("results", [])
        ]
        return movie_data
    return []


def get_movie_details(movie_id):
    """Get detailed movie info from TMDB API."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    headers = {
        "accept": "application/json",
        "Authorization": TMDB_BEARER_TOKEN
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

####################################
# Routes
####################################

@main.route("/")
def root():
    """Homepage route displaying popular movies."""
    user_id = session.get("user_id")
    popular_movies = get_popular_movies()
    return render_template("homepage.html", movies=popular_movies, user_id=user_id)


@main.route("/signup", methods=["GET", "POST"])
def signup():
    """User signup route."""
    form = SignupForm()
    if "user_id" in session:
        flash("You are already logged in")
        return redirect("/")
    if form.validate_on_submit():
        # Check if username is already taken
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.")
            return redirect("/signup")

        first_name = form.first_name.data
        last_name = form.last_name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Generate hashed password
        hashed = bcrypt.generate_password_hash(password)
        hashed_utf8 = hashed.decode("utf8")

        # Create a new TMDB access token if needed
        new_tmdb_access_token = create_tmdb_token()

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=hashed_utf8,
            tmdb_token=new_tmdb_access_token
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect("/")
    return render_template("signup.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    """User login route."""
    if "user_id" in session:
        flash("You are already logged in")
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        unhashed_pwd = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, unhashed_pwd):
            session["user_id"] = user.id
            return redirect("/")
        else:
            flash("Incorrect username or password")
            return redirect("/login")
    return render_template("login.html", form=form)


@main.route("/profile")
def show_profile():
    """Redirect to the logged-in user's profile."""
    if "user_id" not in session:
        flash("Please login first")
        return redirect("/login")
    user_id = session.get("user_id")
    return redirect(url_for("main.user_detail", user_id=user_id))


@main.route("/user/<int:user_id>", methods=["GET"])
def user_detail(user_id):
    """Display a user's profile and their lists."""
    if "user_id" not in session:
        flash("Please login first")
        return redirect("/login")
    if user_id != session.get("user_id"):
        flash("You do not have permission to view this list.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    lists = user.lists
    return render_template("profile.html", user=user, lists=lists)


@main.route("/search", methods=["GET", "POST"])
def search_movie():
    """Search movies by title."""
    form = SearchForm()
    if form.validate_on_submit():
        title = form.title.data
        movie_data = find_movie(title)
        if not movie_data:
            flash("No movies found", "warning")
            return redirect("/search")
        else:
            return render_template("movie.html", movies=movie_data)
    return render_template("search.html", form=form)


@main.route("/movie/<int:movie_id>", methods=["GET", "POST"])
def movie_info(movie_id):
    """Show detailed movie info and allow adding the movie to a user's list."""
    user_id = session.get("user_id")
    movie_details = get_movie_details(movie_id)
    form = UserListForm()
    user = None
    if user_id:
        user = User.query.get(user_id)
        user_lists = user.lists
        form.list_select.choices = [(lst.id, lst.name) for lst in user_lists]
        if form.validate_on_submit():
            selected_list = UserList.query.get(form.list_select.data)
            movies_in_list = [movie.movie_id for movie in selected_list.movies]
            if movie_id in movies_in_list:
                flash("Already in the list")
                return redirect(f"/movie/{movie_id}")
            else:
                movie_to_add = Movie(
                    movie_id=movie_id,
                    title=movie_details.get("title"),
                    poster_path=movie_details.get("poster_path")
                )
                selected_list.movies.append(movie_to_add)
                user.movies.append(movie_to_add)
                db.session.commit()
                flash("Movie added")
                return redirect(f"/list/{selected_list.id}")
    return render_template("movie_detail.html", movie=movie_details, form=form, user_id=user_id, user=user)


@main.route("/list/new", methods=["GET", "POST"])
def create_list():
    """Create a new user list."""
    if "user_id" not in session:
        flash("Please login first to create a list")
        return redirect("/login")
    user_id = session.get("user_id")
    form = AddListForm()
    if form.validate_on_submit():
        name = form.name.data
        new_list = UserList(name=name, user_id=user_id)
        db.session.add(new_list)
        db.session.commit()
        flash("New list created")
        return redirect("/profile")
    return render_template("create_list.html", form=form)


@main.route("/list/<int:list_id>")
def show_list_detail(list_id):
    """Display details for a specific list."""
    if "user_id" not in session:
        flash("Please login first to view the list")
        return redirect("/login")
    user_list = UserList.query.get_or_404(list_id)
    # (Optional) Check that the list belongs to the logged-in user
    if user_list.user_id != session.get("user_id"):
        flash("You do not have permission to view this list.", "danger")
        return redirect("/")
    movies = user_list.movies
    return render_template("list_detail.html", lists=user_list, movies=movies)


@main.route("/list/<int:list_id>/movie/<int:movie_id>/delete")
def remove_movie(list_id, movie_id):
    """Remove a movie from a list."""
    if "user_id" not in session:
        flash("Please login first")
        return redirect("/login")
    user_list = UserList.query.get_or_404(list_id)
    user = User.query.get(session.get("user_id"))
    movie_to_delete = next((movie for movie in user_list.movies if movie.id == movie_id), None)
    if movie_to_delete:
        if movie_to_delete in user.movies:
            user.movies.remove(movie_to_delete)
        user_list.movies.remove(movie_to_delete)
        db.session.commit()
        flash(f"Movie {movie_to_delete.title} has been removed from the list.")
    else:
        flash("Movie not found in the list.")
    return redirect(f"/list/{list_id}")


@main.route("/list/<int:list_id>/rename", methods=["GET", "POST"])
def rename_list(list_id):
    """Rename an existing list."""
    if "user_id" not in session:
        flash("Please log in first")
        return redirect("/login")
    form = RenameListForm()
    if form.validate_on_submit():
        selected_list = UserList.query.get_or_404(list_id)
        selected_list.name = form.new_name.data
        db.session.commit()
        flash("Success")
        return redirect(f"/list/{list_id}")
    return render_template("rename_list.html", form=form)


@main.route("/list/<int:list_id>/delete")
def delete_list(list_id):
    """Delete a user list if it has no movies."""
    if "user_id" not in session:
        flash("You do not have permission to delete this list.", "danger")
        return redirect("/login")
    user_list = UserList.query.get_or_404(list_id)
    if user_list.movies:
        flash("You cannot delete a list that contains movies. Please remove all movies first.", "warning")
        return redirect(f"/list/{list_id}")
    db.session.delete(user_list)
    db.session.commit()
    flash(f'The list "{user_list.name}" has been deleted.', "success")
    return redirect("/profile")


@main.route("/logout")
def logout():
    """Logout the current user."""
    if "user_id" in session:
        session.pop("user_id")
    else:
        flash("You are not logged in")
        return redirect("/login")
    return redirect("/")
