from flask_babel import gettext
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import InputRequired, Email, EqualTo, URL, \
    ValidationError


class ImageURL(URL):
    def __init__(self, message=None):
        if not message:
            message = "Field must be a valid URL to a jpeg, png or gif."
        super(ImageURL, self).__init__(message=message)

    def __call__(self, form, field):
        super(ImageURL, self).__call__(form, field)

        if not any(field.data.endswith(sx) for sx in ['.gif', '.png', '.jpg']):
            raise ValidationError(self.message)


class LoginForm(FlaskForm):
    email = StringField(gettext('E-Mail Address'),
                        validators=[InputRequired()])
    password = PasswordField(gettext('Password'), validators=[InputRequired()])


class SignUpForm(FlaskForm):
    email = StringField(gettext('E-Mail Address'),
                        validators=[InputRequired(), Email()])
    password = PasswordField(gettext('Password'),
                             validators=[InputRequired(),
                                         EqualTo('confirm',
                                                 message='Passwords must match')
                                         ])
    confirm = PasswordField(gettext('Repeat Password'),
                            validators=[InputRequired()])


class QuestionForm(FlaskForm):
    text = StringField(gettext('Question'),
                       validators=[InputRequired()],
                       render_kw={"placeholder": gettext('Enter your question here.')})
    q_type = SelectField(gettext('Type'), choices=[('text', 'Text'), ('image', 'Image'), ('sound', 'Sound')])


class ContributionForm(FlaskForm):
    contribution = SelectField(gettext('Contribution'),
                               choices=[('choice1', 'choice1')])
