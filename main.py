import os
import uuid
from functools import wraps
from random import shuffle

from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_babel import Babel, gettext
from flask_login import LoginManager, login_required, \
    login_user, logout_user, current_user
from flask_wtf import FlaskForm

import helper
from admin import handle_admin, handle_edit_user
from config import ALLOWED_EXTENSIONS
from db_handler import db_session, init_db
from forms import LoginForm, SignUpForm, QuestionForm
from models import User, Round, Participation, Question, Description, Answer

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
    cur_round = helper.get_cur_round()
    form = None
    participation = None
    if cur_round is not None:
        participation = helper.get_cur_participation(cur_round.id)

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
            form = helper.build_description_form(cur_round, helper.get_cur_participation(cur_round.id).description)
    else:
        flash(gettext("There is currently no active round!"))
    return render_template('index.html', active=0, participation=participation, form=form)


@app.route("/add_question", methods=['GET', 'POST'])
@login_required
def add_question():
    cur_round = helper.get_cur_round()

    if cur_round is not None:
        form = QuestionForm()
        if form.validate_on_submit():
            db_session.add(Question(form.text.data, form.q_type.data))
            helper.get_cur_participation(cur_round.id).eligible = True
            db_session.commit()
        else:
            print_errors(form)

    return redirect(url_for('index'))


@app.route("/admin")
@admin_required
@login_required
def admin():
    return handle_admin()


@app.route("/add_round")
@admin_required
@login_required
def add_round():
    if helper.get_cur_round() is None:
        db_session.add(Round())
        db_session.commit()

    return redirect(url_for('admin'))


@app.route("/edit_user")
@admin_required
@login_required
def edit_user():
    return handle_edit_user()


@app.route("/edit_question")
@admin_required
@login_required
def edit_question():
    action = request.args.get('action')
    question = db_session.query(Question).filter(Question.id == request.args.get('id'))[0]
    cur_round = helper.get_cur_round()

    if action == 'use':
        if question in cur_round.questions:
            cur_round.questions.remove(question)
        else:
            cur_round.questions.append(question)

        db_session.commit()
    elif action == 'delete':
        db_session.delete(question)
        db_session.commit()

    return redirect(url_for('admin'))


def file_suffix(filename):
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename):
    return '.' in filename and file_suffix(filename) in ALLOWED_EXTENSIONS


@app.route("/description", methods=['GET', 'POST'])
@login_required
def description():
    form = FlaskForm()
    cur_round = helper.get_cur_round()
    if cur_round is None:
        return redirect(url_for('index'))

    cur_participation = helper.get_cur_participation(cur_round.id)
    if cur_participation is None:
        return redirect(url_for('index'))

    if form.validate_on_submit():
        form = request.form
        files = request.files
        for question in [question for question in form if question.startswith('question')]:
            if form[question] != '':
                q_id = question.rsplit('_', 1)[1]
                answer = helper.get_answer(cur_participation.description.id, q_id)
                if answer is None:
                    cur_question = db_session.query(Question).filter(Question.id == q_id).first()
                    answer = Answer(description=cur_participation.description, question=cur_question)
                    db_session.add(answer)

                answer.text = form[question]
                db_session.commit()

        for file_field in files:
            u_file = files[file_field]
            if u_file.filename != '':
                q_id = file_field.rsplit('_', 1)[1]
                answer = helper.get_answer(cur_participation.description.id, q_id)
                if answer is None:
                    cur_question = db_session.query(Question).filter(Question.id == q_id).first()
                    answer = Answer(description=cur_participation.description, question=cur_question)
                    db_session.add(answer)

                filename = str(uuid.uuid4())
                new_filename = "{}.{}".format(filename, file_suffix(u_file.filename))
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                u_file.save(file_path)

                answer.text = new_filename
                db_session.commit()

    else:
        print_errors(form)
    return redirect(url_for('index'))


@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


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
    init_db()

    app.debug = True
    app.run(host='0.0.0.0')
