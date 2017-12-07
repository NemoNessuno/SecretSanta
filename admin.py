from itertools import ifilter

from flask import render_template, url_for, request
from flask_login import current_user
from werkzeug.utils import redirect

from db_handler import db_session
from helper import get_cur_round
from models import Round, Question, User, Participation


def handle_admin():
    rounds = db_session.query(Round).all()
    questions = db_session.query(Question).all()

    users = db_session.query(User).all()
    current_round = next(ifilter(lambda cur_round: cur_round.running, rounds), None)

    for question in questions:
        question.in_cur_round = question in current_round.questions
        question.in_use = question.in_cur_round or any([(question in a_round.questions) for a_round in rounds])

    participations = []
    if current_round is not None:
        participations = db_session.query(Participation).filter(Participation.round_id == current_round.id).all()

    return render_template('admin.html', active=2,
                           rounds=rounds,
                           participations=participations,
                           current_round=current_round,
                           questions=questions,
                           users=users)


def handle_edit_user():
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


def handle_question_edit():
    action = request.args.get('action')
    question = db_session.query(Question).filter(Question.id == request.args.get('id'))[0]
    cur_round = get_cur_round()

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
