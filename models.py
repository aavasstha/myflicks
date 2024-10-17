from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt=Bcrypt()

# Association table for the many-to-many relationship between User and Movie
user_movie_association = db.Table('user_movie',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for the many-to-many relationship between User and UserList
user_list_association = db.Table('user_list',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('list_id', db.Integer, db.ForeignKey('watch_lists.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for the many-to-many relationship between UserList and Movie
list_movie_association = db.Table('list_movie',
    db.Column('list_id', db.Integer, db.ForeignKey('watch_lists.id', ondelete='CASCADE'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    tmdb_token = db.Column(db.Text, nullable=False, unique=True)
    lists = db.relationship('UserList', backref='user', lazy=True)
    movies = db.relationship('Movie', secondary=user_movie_association, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return f'<User username:{self.username}>'


class UserList(db.Model):
    __tablename__ = 'watch_lists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movies = db.relationship('Movie', secondary='list_movie', backref=db.backref('lists', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Listname: {self.name}>'

class Movie(db.Model):
    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.Text, nullable=False)
    poster_path = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Movie id: {self.id} title: {self.title}>'

def connect_db(app):
    """Connect to database """
    db.app = app
    db.init_app(app)

