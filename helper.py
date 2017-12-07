from itertools import ifilter

from flask_babel import gettext
from flask_login import current_user
from sqlalchemy import and_
from wtforms import StringField, FileField

from db_handler import db_session
from forms import DescriptionForm, Length
from models import Participation, Round, Answer


def build_description_form(current_round, current_description):
    form = DescriptionForm

    for question in current_round.questions:
        field = None
        answer = get_answer(current_description.id, question.id)
        answer_text = '' if answer is None else answer.text
        if question.q_type == 'text':
            field = StringField(question.text,
                                render_kw={"placeholder": gettext('Type your answer here.')},
                                default=answer_text, description=question.q_type,
                                validators=[Length(max=256)])
        else:
            field = FileField(question.text, default=answer_text, description=question.q_type)

        setattr(form, 'question_{}'.format(question.id), field)

    return form()


def get_cur_participation(cur_rounds_id):
    participations = db_session.query(Participation).filter(Participation.round_id == cur_rounds_id).all()
    participation = next(
        ifilter(lambda part: part.description.user_id == current_user.email,
                participations), None)
    return participation


def get_cur_round():
    cur_rounds = db_session.query(Round).filter(Round.running).all()

    if len(cur_rounds) > 0:
        return cur_rounds[0]
    else:
        return None


def get_answer(description_id, question_id):
    return db_session.query(Answer).filter(and_(
        Answer.description_id == description_id,
        Answer.question_id == question_id
    )).first()
