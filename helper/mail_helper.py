from flask import url_for, render_template
from flask_mail import Message


def send_mail(mail, address, subject, html):
    with mail.connect() as conn:
        msg = Message(subject,
                sender="secret@santa.com",
                recipients=[address])
        msg.html = html
        conn.send(msg)


def send_reset_mail(mail, address, token):
    subject = "Want to reset your password?"

    reset_url = url_for(
        'reset_password',
        token=token,
        _external=True)

    html = render_template(
        'email/reset_link.html',
        reset_url=reset_url)

    send_mail(mail, address, subject, html)
