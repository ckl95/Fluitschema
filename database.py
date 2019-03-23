from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from waitress import serve

# The flask application pacakage

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://cmqnzhslytdnff:96d89452b06747de32826f75925a2edb7406b343fcdedd774bb04aec262adf5c@ec2-23-21-165-188.compute-1.amazonaws.com:5432/dkgb8euqaflh"
database = SQLAlchemy(app)

serve(app, host="127.0.0.1", port=5000)
