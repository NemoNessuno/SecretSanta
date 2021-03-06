from flask import render_template, url_for, request
from flask_login import current_user
from werkzeug.utils import redirect

import helper.generic_helper as helper
from db_handler import db_session
from models import Round, Question, User, Participation, Description


def handle_admin():
    rounds = db_session.query(Round).all()
    questions = db_session.query(Question).all()

    users = db_session.query(User).all()
    current_round = next(filter(lambda cur_round: cur_round.running, rounds), None)

    participations = []
    if current_round is not None:
        for question in questions:
            question.in_cur_round = question in current_round.questions
            question.in_use = question.in_cur_round or any([(question in a_round.questions) for a_round in rounds])
 
        participations = db_session.query(Participation).filter(Participation.round_id == current_round.id).all()
        for participation in participations:
            unanswered = []
            for question in current_round.questions:
                answer = helper.get_answer(participation.description_id,
                        question.id)
                if answer is None or answer.text.isspace():
                    unanswered.append(question.text)
            participation.description.unanswered = unanswered
            participation.description.is_filled = len(unanswered) == 0

    shall_shuffle = all([participation.description.is_filled for participation in participations]) \
                    and not any([participation.other_description for participation in participations])

    return render_template('admin.html', active=1, is_admin=True,
                           rounds=rounds,
                           participations=participations,
                           shall_shuffle=shall_shuffle,
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


def handle_edit_question():
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


def handle_edit_round(action):
    cur_round = helper.get_cur_round()

    if action == 'add':
        if cur_round is None:
            db_session.add(Round())
            db_session.commit()
    elif action == 'stop':
        if cur_round is not None:
            cur_round.running = False
            db_session.commit()
    elif action == 'shuffle':
        if cur_round is not None:
            participations = helper.get_cur_participations(cur_round.id)
            random_indizes = helper.random_derangement(len(participations))
            for index in range(len(participations)):
                participations[index].other_description = participations[random_indizes[index]].description

            db_session.commit()
    return redirect(url_for('admin'))


def handle_edit_participation(action):
    if action == 'add':
        cur_round = helper.get_cur_round()

        if cur_round is not None:
            participation = Participation(
                cur_round=cur_round,
                description=Description(
                    user=current_user)
            )

            db_session.add(participation)
            db_session.commit()
        return redirect(url_for('index'))

    elif action == 'remove':
        if not (current_user.is_admin()):
            return redirect(url_for('index'))

        part_id = request.args.get('id')
        db_session.query(Participation).filter(Participation.id == part_id).delete()
        db_session.commit()

        return redirect(url_for('admin'))
