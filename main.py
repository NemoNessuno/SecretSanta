from random import shuffle

from flask import Flask, render_template, redirect, url_for, flash
from flask_babel import Babel, gettext
from flask_login import LoginManager, login_required, \
    login_user, logout_user, current_user

from db_handler import db_session
from forms import LoginForm, SignUpForm
from models import User, Round, Participation

# Initialize the base app and load the config
app = Flask(__name__)
app.config.from_object('config')

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize Babel for I18n
babel = Babel(app)


@app.teardown_appcontext
def close_db(exception=None):
    db_session.remove()


@login_manager.user_loader
def user_loader(identifier):
    return User.query.get(identifier)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.get(form.email.data)
        if user is not None:
            user.validated = user.password == form.password.data
            if user.validated:
                login_user(user)
                return redirect(url_for('index'))
        flash(gettext(u"Error with entered e-mail or password."))
    else:
        print_errors(form)

    return render_template("login.html", form=form, active=-1)


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    cur_rounds = db_session.query(Round).filter(Round.running).all()
    if len(cur_rounds) > 0:
        participation = db_session.query(Participation).filter(Participation.round_id == cur_rounds[0].id)
    else:
        flash(gettext("There is currently no active round!"))
    return render_template('index.html', active=0)


@app.route("/admin")
@login_required
def admin():
    return render_template('admin.html', active=-1)


@app.route("/description")
@login_required
def description():
    return render_template('description.html', active=1,
                           description=current_user.description)


@app.route("/gallery")
@login_required
def gallery():
    descriptions = [user.description for user in User.query.all()]
    shuffle(descriptions)

    return render_template('gallery.html', active=0,
                           descriptions=descriptions)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        user = User()
        user.email = form.email.data
        user.password = form.password.data
        user.authenticated = True
        db_session.add(user)
        db_session.commit()
        login_user(user)
        return redirect(url_for('index'))
    else:
        print_errors(form)

    return render_template("signup.html", form=form, active=-1)


def print_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(gettext(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error)))


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
