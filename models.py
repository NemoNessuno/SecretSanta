from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date, Table, Enum
from sqlalchemy.orm import validates, relationship

from db_handler import Base
from password import Password


class User(Base):
    __tablename__ = 'users'
    email = Column(String(120), unique=True, primary_key=True)
    password = Column(Password)
    admin = Column(Boolean)

    # Or specify a cost factor other than the default 12
    # password = Column(Password(rounds=10))

    @validates('password')
    def _validate_password(self, key, password):
        self.validated = getattr(type(self), key).type.validator(password)
        return self.validated

    def is_active(self):
        return True

    def get_id(self):
        return self.email

    def is_authenticated(self):
        return self.validated

    def is_admin(self):
        return self.admin

    def is_anonymous(self):
        return False

    def __init__(self, email=None, admin=False):
        self.email = email
        self.admin = admin
        self.validated = False

    def __repr__(self):
        return '<User %r>' % self.email


class Round(Base):
    __tablename__ = 'rounds'
    id = Column(Integer, primary_key=True)
    running = Column(Boolean)
    created_at = Column(Date)

    def __init__(self, running=True, created_at=datetime.now()):
        self.running = running
        self.created_at = created_at


class Participation(Base):
    __tablename__ = 'participations'
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('rounds.id'))
    cur_round = relationship("Round", foreign_keys=[round_id])
    description_id = Column(Integer, ForeignKey('descriptions.id'))
    description = relationship("Description", foreign_keys=[description_id])
    other_description_id = Column(Integer, ForeignKey('descriptions.id'))
    other_description = relationship("Description", foreign_keys=[other_description_id])
    eligible = Column(Boolean)

    def __init__(self, cur_round=None, description=None, other_description=None, eligible=False):
        self.cur_round = cur_round
        self.description = description
        self.other_description = other_description
        self.eligible = eligible


description_questions = Table(
    'association', Base.metadata,
    Column('description_id', Integer, ForeignKey('descriptions.id')),
    Column('question_id', Integer, ForeignKey('questions.id'))
)


class Description(Base):
    __tablename__ = 'descriptions'
    id = Column('id', Integer, primary_key=True)
    user_id = Column(String(120), ForeignKey('users.email'))
    user = relationship("User", foreign_keys=[user_id])
    questions = relationship("Question", secondary=description_questions)

    def __init__(self, user=None, questions=None):
        if questions is None:
            questions = []
        self.user = user
        self.questions = questions

    def is_filled(self):
        return len(self.questions) > 0 and all([len(question.text) > 0 for question in self.questions])


class Question(Base):
    __tablename__ = 'questions'
    id = Column('id', Integer, primary_key=True)
    text = Column(String(256))
    q_type = Column('type', Enum('text', 'image', 'sound'))

    def __init__(self, text=None, q_type='text'):
        self.text = text
        self.q_type = q_type

