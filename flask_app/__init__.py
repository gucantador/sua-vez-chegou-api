from flask import Flask
from flask_sock import Sock
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
#from flask_jwt_extended import JWTManager
#from datetime import timedelta
from flask_cors import CORS
import os
#load_dotenv()

#DATABASE_URI = os.getenv('DATABASE_URI')

app = Flask(__name__)
sock = Sock(app)# creates a flask app with the name of the file as a parameter
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URI")
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
#app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
#app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
#app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
#jwt__ = JWTManager(app)
db = SQLAlchemy(app) # initialize sqlalchemy object
migrate = Migrate(app, db)

from flask_app import routes
