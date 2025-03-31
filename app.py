from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from models import db, connect_db
from flask_debugtoolbar import DebugToolbarExtension
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres.eduudvvgrhjpnkrjuegx:Ao0hwJxHQKfDpQCd@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] =  'my-very-secret-key'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Connect to the database
connect_db(app)
db.create_all()

# Initialize Debug Toolbar
DebugToolbarExtension(app)

# Import and register the blueprint
from routes import main as main_routes
app.register_blueprint(main_routes)

if __name__ == '__main__':
    app.run(debug=True)
