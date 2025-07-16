from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import LoginManager
from routes import views
from models import User, db
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

app.jinja_env.globals['gravatar'] = gravatar  # make gravatar global to templates


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI", "sqlite:///posts.db")
db.init_app(app)


with app.app_context():
    db.create_all()


app.register_blueprint(views)  # register the views from routes

if __name__ == "__main__":
    app.run(debug=False, port=5001)
