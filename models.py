from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import validates, relationship
from db_handler import Base
from password import Password


class User(Base):
    __tablename__ = 'users'
    email = Column(String(120), unique=True, primary_key=True)
    password = Column(Password)
    contribution = Column('contribution_id',
                          ForeignKey('contributions.contribution_id'))
    description_id = Column(Integer,
                            ForeignKey('descriptions.description_id'))
    description = relationship("Description", foreign_keys=[description_id])
    other_description_id = Column(Integer,
                                  ForeignKey('descriptions.description_id'))
    other_description = relationship("Description",
                                     foreign_keys=[other_description_id])
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

    def is_anonymous(self):
        return False

    def __init__(self, email=None, contribution=None, description=None):
        self.email = email
        self.contribution = contribution
        self.description = description
        self.validated = False

    def __repr__(self):
        return '<User %r>' % (self.email)


class Contribution(Base):
    __tablename__ = 'contributions'
    id = Column('contribution_id', Integer, primary_key=True)
    description = Column(String(120), nullable=False)

    def __init__(self, description=None):
        self.description = description


class Description(Base):
    __tablename__ = 'descriptions'
    id = Column('description_id', Integer, primary_key=True)
    person = Column(String(256), nullable=False)
    place = Column(String(256), nullable=False)
    quote = Column(String(256), nullable=False)
    theme = Column(String(256), nullable=False)
    saturday = Column(String(256), nullable=False)

    def __init__(self, person=None, place=None,
                 quote=None, theme=None, saturday=None):
        self.person = person
        self.place = place
        self.quote = quote
        self.theme = theme
        self.saturday = saturday
