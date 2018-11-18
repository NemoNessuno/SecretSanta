from functools import wraps
from random import shuffle

from flask import Flask, render_template, redirect, url_for, flash, send_from_directory, request
from flask_babel import Babel, gettext
from flask_login import LoginManager, login_required, \
    login_user, logout_user, current_user

from flask_mail import Mail

from itsdangerous import URLSafeTimedSerializer

import helper.generic_helper as generic_helper, helper.mail_helper as mail_helper
from admin import handle_admin, handle_edit_user, handle_edit_question, \
handle_edit_round, handle_edit_participation
from db_handler import db_session, init_db
from description import handle_description_form
from forms import LoginForm, SignUpForm, QuestionForm, \
RequestResetPasswordForm, ResetPasswordForm
from models import User, Question

# Initialize the base app and load the config
app = Flask(__name__, instance_relative_config=True)
app.config.from_envvar('FLASK_CONFIG')

# Initialize the mail
mail = Mail()
mail.init_app(app)

# Initialize 
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

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
        generic_helper.print_errors(form)

    return render_template("login.html", form=form, active=-1)


@app.route('/request_reset_password', methods=['GET', 'POST'])
def request_reset_password():
# Now we'll send the email confirmation link
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(form.email.data)
        if user is not None:
            email_address = user.email
     
            token = ts.dumps(email_address, salt='reset-password-key')
            mail_helper.send_reset_mail(mail, user.email, token)
            flash(gettext(u"E-Mail has been sent. Please check your \
                    inbox."))
            
            return redirect(url_for('index'))

        flash(gettext(u"Error! E-Mail not in database"))
    else:
        generic_helper.print_errors(form)
        
    return render_template("request_reset_password.html", form=form, active=-1)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()
    
    try:
        email = ts.loads(token, salt="reset-password-key", max_age=1800)
    except:
        flash(gettext(u"Invalid token. Maybe it is outdated."))
        return redirect(url_for('index'))

    if form.validate_on_submit():
        user = User.query.get(email)
        user.password = form.password.data
        
        db_session.add(user)
        db_session.commit()
        
        flash(gettext(u"Password changed successfully."))
        return redirect(url_for('index'))
    else:
        generic_helper.print_errors(form)   
    
    
    return render_template("reset_pw.html", token=token, form=form, active=-1)

@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    cur_round = generic_helper.get_cur_round()
    form = None
    desc = None
    participation = None
    can_participate = False
    if cur_round is not None:
        participation = generic_helper.get_cur_participation(cur_round.id)

        if participation is not None:
            if not participation.eligible:
                form = QuestionForm()
            elif participation.other_description:
                desc = generic_helper.build_description(cur_round.questions, participation.other_description.id)
            else:
                form = generic_helper.build_description_form(cur_round, generic_helper.get_cur_participation(cur_round.id).description)
        else:
            participations = generic_helper.get_cur_participations(cur_round.id)
            can_participate = all([not l_participation.other_description for l_participation in participations])
    return render_template('index.html', active=0, is_admin=current_user.is_admin(),
                           active_round=cur_round is not None,
                           participation=participation,
                           can_participate=can_participate,
                           description=desc, form=form)


@app.route("/edit_participation")
@login_required
def edit_participation():
    action = request.args.get('action')
    return handle_edit_participation(action)


@app.route("/add_question", methods=['GET', 'POST'])
@login_required
def add_question():
    cur_round = generic_helper.get_cur_round()

    if cur_round is not None:
        form = QuestionForm()
        if form.validate_on_submit():
            db_session.add(Question(form.text.data, form.q_type.data))
            generic_helper.get_cur_participation(cur_round.id).eligible = True
            db_session.commit()
        else:
            generic_helper.print_errors(form)

    return redirect(url_for('index'))


@app.route("/admin")
@admin_required
@login_required
def admin():
    return handle_admin()


@app.route("/edit_round/<action>")
@admin_required
@login_required
def edit_round(action):
    return handle_edit_round(action)


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
@admin_required
@login_required
def gallery():
    cur_round = generic_helper.get_cur_round()

    if cur_round is None:
        return redirect(url_for('admin'))
    else:
        descriptions = [
            generic_helper.build_description(cur_round.questions, participation.description_id)
            for participation in generic_helper.get_cur_participations(cur_round.id)
        ]
        shuffle(descriptions)

    return render_template('gallery.html', active=2, is_admin=True,
                           descriptions=descriptions)


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit(): 
        user = User.query.get(form.email.data)
        if user is None:
            user = User()
            user.email = form.email.data
            user.password = form.password.data
            user.admin = db_session.query(User).count() < 1
            user.authenticated = True
            db_session.add(user)
            db_session.commit()
            login_user(user)
        else:
            flash(gettext(u"A user with this email already exists."))
        return redirect(url_for('index'))
    else:
        generic_helper.print_errors(form)

    return render_template("signup.html", form=form, active=-1)


if __name__ == "__main__":
    init_db()

    app.debug = True
    app.run(host='0.0.0.0')
