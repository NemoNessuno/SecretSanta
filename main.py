from functools import wraps
from random import shuffle

from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, request
from flask_babel import Babel, gettext
from flask_login import LoginManager, login_required, \
    login_user, logout_user, current_user

import helper
from admin import handle_admin, handle_edit_user, handle_edit_question, handle_edit_round, handle_edit_participation
from db_handler import db_session, init_db
from description import handle_description_form
from forms import LoginForm, SignUpForm, QuestionForm
from models import User, Question

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
        if current_user is not User and not current_user.is_admin():
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
        helper.print_errors(form)

    return render_template("login.html", form=form, active=-1)


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    cur_round = helper.get_cur_round()
    form = None
    desc = None
    participation = None
    can_participate = False
    if cur_round is not None:
        participation = helper.get_cur_participation(cur_round.id)

        if participation is not None:
            if not participation.eligible:
                form = QuestionForm()
            elif participation.other_description:

                desc = [{
                    'question': question,
                    'answer': helper.get_answer(participation.other_description_id, question.id)
                } for question in cur_round.questions]
            else:
                form = helper.build_description_form(cur_round, helper.get_cur_participation(cur_round.id).description)
        else:
            participations = helper.get_cur_participations(cur_round.id)
            can_participate = all([not l_participation.other_description for l_participation in participations])
    else:
        flash(gettext("There is currently no active round!"))
    return render_template('index.html', active=0,
                           active_round=cur_round is not None,
                           participation=participation,
                           can_participate=can_participate,
                           desc=desc, form=form)


@app.route("/edit_participation")
@login_required
def edit_participation():
    action = request.args.get('action')
    return handle_edit_participation(action)


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
            helper.print_errors(form)

    return redirect(url_for('index'))


@app.route("/admin")
@admin_required
@login_required
def admin():
    return handle_admin()


@app.route("/edit_round")
@admin_required
@login_required
def edit_round():
    return handle_edit_round()


@app.route("/edit_user")
@admin_required
@login_required
def edit_user():
    return handle_edit_user()


@app.route("/edit_question")
@admin_required
@login_required
def edit_question():
    return handle_edit_question()


@app.route("/description", methods=['GET', 'POST'])
@login_required
def description():
    return handle_description_form(app.config)


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
        helper.print_errors(form)

    return render_template("signup.html", form=form, active=-1)


if __name__ == "__main__":
    init_db()

    app.debug = True
    app.run(host='0.0.0.0')
