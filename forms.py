from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import InputRequired, Email, EqualTo, URL, \
    ValidationError
from flask_babel import gettext


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


class DescriptionForm(FlaskForm):
    person = StringField(gettext(
        'Which famous person (fictional or real) describes you the best?'),
        validators=[InputRequired(), ImageURL()],
        render_kw={"placeholder": gettext('Please enter a valid image url.')})
    saturday = StringField(gettext(
        'What does a perfect saturday evening look like for you?'),
        validators=[InputRequired()])
    place = StringField(gettext('Where would you like to be right now?'),
                        validators=[InputRequired()])
    quote = StringField(gettext('What is your favourite quote?'),
                        validators=[InputRequired()])
    theme = StringField(gettext(
        'What background theme should play in your life?'),
        validators=[InputRequired()])


class ContributionForm(FlaskForm):
    contribution = SelectField(gettext('Contribution'),
                               choices=[('choice1', 'choice1')])
