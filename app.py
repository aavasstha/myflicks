from flask import Flask, render_template, redirect, session, flash
import requests
from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from forms import SignupForm, LoginForm, SearchForm, AddListForm, UserListForm, RenameListForm
from models import db, connect_db, User, UserList, Movie
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SUPABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
TMDB_BEARER_TOKEN=os.getenv('TMDB_BEARER_TOKEN')
connect_db(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)
bcrypt=Bcrypt()


def get_popular_movies():
    url = "https://api.themoviedb.org/3/movie/popular?language=en-US&page=1"
    headers = {
    "accept": "application/json",
    "Authorization": TMDB_BEARER_TOKEN}   
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
        for result in data['results']
    ]
        return extracted_data
    else:
        flash("something went wrong.")
        return render_template("404.html")

def create_tmdb_token():
    url = "https://api.themoviedb.org/3/authentication/token/new"
    headers = {
    "accept": "application/json",
    "Authorization": TMDB_BEARER_TOKEN
}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        access_token = data.get('request_token') 
    else:
        flash("Failed to retrieve access token")
    return access_token

# homepage route
@app.route("/")
def root(): 
    user_id=session.get('user_id')
    popular_movies = get_popular_movies()
    return render_template('homepage.html', movies=popular_movies, user_id=user_id)


# Signup form route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    # signup form instance
    form = SignupForm()
    if "user_id" in session:
        flash("You are already logged in")
        return redirect("/")
    if form.validate_on_submit():
        users=[user.username for user in User.query.all()]
        if  form.username.data not in users:
            # collecting form data
            first_name=form.first_name.data
            last_name=form.last_name.data
            username=form.username.data
            email=form.email.data
            password=form.password.data

            # generating password hash
            hashed = bcrypt.generate_password_hash(password)
            hashed_utf8=hashed.decode("utf8")

            # creating new User class instance with hashed password
            new_tmdb_access_token = create_tmdb_token()
            new_user = User(first_name=first_name, last_name=last_name, username=username, email=email, password=hashed_utf8, tmdb_token=new_tmdb_access_token)

            # add to database
            db.session.add(new_user)
            db.session.commit()
            # return render_template('homepage.html', form=form)
            return redirect("/")
        else:
            flash("Username already taken.")
            return redirect("/signup")

    return render_template('signup.html', form=form)


# Login form route
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        flash("You are already logged in")
        return redirect("/")
    # login form instance
    form=LoginForm()
    if form.validate_on_submit():

        
        # collecting form data
        username=form.username.data
        unhashed_pwd = form.password.data
        
        #validate user
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, unhashed_pwd):
            # add user to session
            session['user_id'] = user.id
            return redirect(f"/")
        else:
            flash('Incorrect username or password')
            return redirect("/login")
                    
    return render_template("login.html", form=form)

# User profile route
@app.route('/profile')
def show_profile():
    if "user_id" not in session:
        flash("Please login first")
        return redirect('/login')
    user_id=session.get('user_id')
    return redirect(f'/user/{user_id}')

# User profile route
@app.route("/user/<int:user_id>", methods=["GET"])
def user_detail(user_id):
    if "user_id" not in session:
        flash("Please login first")
        return redirect('/login')
    user=User.query.get(user_id)
    lists=user.lists
    return render_template("profile.html", user=user, lists=lists)

# Search movie function (returns list of movie)
def find_movie(title):
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
        for result in data['results']
    ]
        return movie_data
    
# search movies
@app.route("/search", methods=["GET", "POST"])
def search_movie():
    form=SearchForm()
    title = form.title.data
    if form.validate_on_submit():
        movie_data=find_movie(title)
        if not movie_data:
            flash("No movies found", "warning")
            return redirect("/search")
        else:
            return render_template("movie.html", movies=movie_data)
    return render_template("search.html", form=form)


# get full movie details 
def get_movie_details(movie_id):
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

# show movie detail
@app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
def movie_info(movie_id):
    user_id = session.get('user_id')
    movie_details = get_movie_details(movie_id)
    form = UserListForm()
    
    user = None  # Initialize user to None

    if user_id:
        user = User.query.get(user_id)
        user_lists = user.lists
        form.list_select.choices = [(user_list.id, user_list.name) for user_list in user_lists]
        selected_list = None
        
        if form.validate_on_submit():
            # Get the selected list
            selected_list = UserList.query.get(form.list_select.data)
            movies_in_list = [movie.movie_id for movie in selected_list.movies]
            if movie_id in movies_in_list:
                flash("Already in the list")
                return redirect(f'/movie/{movie_id}')
            else:
                # create new movie 
                movie_to_add = Movie(movie_id=movie_id, title=movie_details.get('title'), poster_path=movie_details.get("poster_path"))
                # add movie to list
                selected_list.movies.append(movie_to_add)
                # append movie 
                user.movies.append(movie_to_add) 
                db.session.commit()
                flash("Movie added")
                return redirect(f"/list/{selected_list.id}")

    return render_template('movie_detail.html', movie=movie_details, form=form, user_id=user_id, user=user)

# route to create new list
@app.route("/list/new", methods=["GET", "POST"])
def create_list():
    if "user_id" not in session:
        flash("Please login first to create list")
        return redirect('/login')
    user_id=session.get("user_id")
    form=AddListForm()
    if form.validate_on_submit():
        name=form.name.data
        new_lsit=UserList(name=name, user_id=user_id)
        db.session.add(new_lsit)
        db.session.commit()
        flash("New list created")
        return redirect("/profile")
    return render_template("create_list.html", form=form)

# route to list detail
@app.route("/list/<int:list_id>")
def show_list_detail(list_id):
    if "user_id" not in session:
        flash("Please login first to view list")
        return redirect('/login')
    list=UserList.query.get(list_id)
    movies=list.movies
    return render_template("list_detail.html", lists=list, movies=movies)

# route to removing movie from a list
@app.route("/list/<int:list_id>/movie/<int:movie_id>/delete")
def remove_movie(movie_id, list_id):
    if("user_id" in session):
        user_list=UserList.query.get_or_404(list_id)
        user=User.query.get(session.get('user_id'))
        movie_to_delete = next((movie for movie in user_list.movies if movie.id == movie_id), None)
        if movie_to_delete:
            user.movies.remove(movie_to_delete)
            user_list.movies.remove(movie_to_delete)
            db.session.commit()
            flash(f"Movie {movie_to_delete.title} has been removed from the list.")
        else:
            flash("Movie not found in the list.")
    return redirect(f"/list/{list_id}")
    
# route to rename list
@app.route("/list/<int:list_id>/rename", methods=["GET", "POST"])
def rename_list(list_id):
    if "user_id" in session:
        form=RenameListForm()

        if form.validate_on_submit():
            selected_list=UserList.query.get_or_404(list_id)
            selected_list.name=form.new_name.data
            db.session.commit()
            flash("Success")
            return redirect(f"/list/{list_id}")
    else:
        flash("Please log in first")
        return redirect("/login")
    return render_template('rename_list.html', form=form)

# route to delete list
@app.route("/list/<int:list_id>/delete")
def delete_list(list_id):
# Get the user's list
    user_list = UserList.query.get_or_404(list_id)
    # Ensure the list belongs to the current user
    if "user_id" not in session:
        flash('You do not have permission to delete this list.', 'danger')
        return redirect("/login")
    # Check if the list has any associated movies
    if user_list.movies:
        flash('You cannot delete a list that contains movies. Please remove all movies first.', 'warning')
        return redirect(f"/list/{list_id}")
    
    # Delete the list
    db.session.delete(user_list)
    db.session.commit()

    flash(f'The list "{user_list.name}" has been deleted.', 'success')
    return redirect("/profile")

# Logout route
@app.route("/logout")
def logout():
    # remove user from session
    if "user_id" in session:
        session.pop('user_id')
    else:
        flash("You are not logged in")
        return redirect("/login")
    return redirect('/')
    