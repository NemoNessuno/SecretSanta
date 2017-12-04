from functools import wraps
from itertools import ifilter
from random import shuffle

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_babel import Babel, gettext
from flask_login import LoginManager, login_required, \
    login_user, logout_user, current_user

from db_handler import db_session
from forms import LoginForm, SignUpForm, QuestionForm
from models import User, Round, Participation, Question, Description

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


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return unauthorized()
        return func(*args, **kwargs)

    return decorated_view


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
    cur_round = get_cur_round()
    form = None
    if cur_round is not None:
        participation = get_cur_participation(cur_round.id)

        if participation is None:
            participation = Participation(
                cur_round=cur_round,
                description=Description(
                    user=current_user)
            )
            db_session.add(participation)
            db_session.commit()

        if not participation.eligible:
            form = QuestionForm()
    else:
        flash(gettext("There is currently no active round!"))
    return render_template('index.html', active=0, participation=participation, form=form)


def get_cur_participation(cur_rounds_id):
    participations = db_session.query(Participation).filter(Participation.round_id == cur_rounds_id).all()
    participation = next(
        ifilter(lambda part: part.description.user_id == current_user.email,
                participations), None)
    return participation


@app.route("/add_question", methods=['GET', 'POST'])
@login_required
def add_question():
    cur_round = get_cur_round()

    if cur_round is not None:
        form = QuestionForm()
        if form.validate_on_submit():
            db_session.add(Question(form.text.data, form.q_type.data))
            get_cur_participation(cur_round.id).eligible = True
            db_session.commit()
        else:
            print_errors(form)

    return redirect(url_for('index'))


def get_cur_round():
    cur_rounds = db_session.query(Round).filter(Round.running).all()

    if len(cur_rounds) > 0:
        return cur_rounds[0]
    else:
        return None


@app.route("/admin")
@admin_required
@login_required
def admin():
    rounds = db_session.query(Round).all()
    questions = db_session.query(Question).all()
    users = db_session.query(User).all()
    current_round = next(ifilter(lambda cur_round: cur_round.running, rounds), None)

    participations = []
    if current_round is not None:
        participations = db_session.query(Participation).filter(Participation.round_id == current_round.id).all()

    return render_template('admin.html', active=2,
                           rounds=rounds,
                           participations=participations,
                           current_round=current_round,
                           questions=questions,
                           users=users)


@app.route("/add_round")
@admin_required
@login_required
def add_round():
    if len(get_cur_round()) < 1:
        db_session.add(Round())
        db_session.commit()

    return redirect(url_for('admin'))


@app.route("/edit_user")
@admin_required
@login_required
def edit_user():
    action = request.args.get('action')
    user = db_session.query(User).filter(User.email == request.args.get('mail'))[0]

    if user.email != current_user.email:
        if action == 'admin':
            user.admin = not user.admin
            db_session.commit()
        elif action == 'delete':
            db_session.delete(user)
            db_session.commit()

    return redirect(url_for('admin'))


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
        user.admin = len(db_session.query(User).all()) < 1
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
