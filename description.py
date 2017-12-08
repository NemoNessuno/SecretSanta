import os
import uuid

from flask import url_for, request
from flask_wtf import FlaskForm
from werkzeug.utils import redirect

from config import ALLOWED_EXTENSIONS
from db_handler import db_session
from helper import get_answer, get_cur_round, get_cur_participation, print_errors
from models import Answer, Question


def file_suffix(filename):
    return filename.rsplit('.', 1)[1].lower()


def allowed_file(filename):
    return '.' in filename and file_suffix(filename) in ALLOWED_EXTENSIONS


def handle_description_form(config):
    form = FlaskForm()
    cur_round = get_cur_round()
    if cur_round is None:
        return redirect(url_for('index'))

    cur_participation = get_cur_participation(cur_round.id)
    if cur_participation is None:
        return redirect(url_for('index'))

    if form.validate_on_submit():
        form = request.form
        files = request.files
        for question in [question for question in form if question.startswith('question')]:
            if form[question] != '':
                q_id = question.rsplit('_', 1)[1]
                answer = get_answer(cur_participation.description.id, q_id)
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
                answer = get_answer(cur_participation.description.id, q_id)
                if answer is None:
                    cur_question = db_session.query(Question).filter(Question.id == q_id).first()
                    answer = Answer(description=cur_participation.description, question=cur_question)
                    db_session.add(answer)

                filename = str(uuid.uuid4())
                new_filename = "{}.{}".format(filename, file_suffix(u_file.filename))
                file_path = os.path.join(config['UPLOAD_FOLDER'], new_filename)
                u_file.save(file_path)

                answer.text = new_filename
                db_session.commit()

    else:
        print_errors(form)
    return redirect(url_for('index'))
