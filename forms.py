
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import EmailField
from models import UserList

class SignupForm(FlaskForm):
    first_name=StringField("First Name", validators=[DataRequired('Please enter your first name.')])
    last_name=StringField("Last Name", validators=[DataRequired('Please enter your last name. ')])
    username=StringField("Username", validators=[DataRequired('Please create a unique username.')])
    email=EmailField("Email", validators=[DataRequired('Please enter a valid email')])
    password =PasswordField("Password", validators=[DataRequired('Plase create a password')])

class LoginForm(FlaskForm):
    username=StringField("Username", validators=[DataRequired('Please enter your username')])
    password =PasswordField("Password", validators=[DataRequired('Plase enter your password')])

class SearchForm(FlaskForm):
    title=StringField("Movie Title", validators=[DataRequired('Please enter a movie title')])


class AddListForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired('Please enter a list name')])

class RenameListForm(FlaskForm):
    new_name = StringField("New Name", validators=[DataRequired('Please enter the new name')])

    
class UserListForm(FlaskForm):
    list_select = SelectField('Choose a List', choices=[], coerce=int, validators=[DataRequired()])
