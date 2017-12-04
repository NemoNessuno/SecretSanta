import random
import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('sqlite:///database.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    from models import User, Description, Round, Participation, description_questions, Question, Answer
    User.__table__.create(bind=engine)
    Round.__table__.create(bind=engine)
    Participation.__table__.create(bind=engine)
    description_questions.create(bind=engine)
    Description.__table__.create(bind=engine)
    Question.__table__.create(bind=engine)
    Answer.__table__.create(bind=engine)
    db_session.commit()


def shuffle():
    descriptions = Description.query.all()
    indizes = random_derangement(len(descriptions))

    for idx, user in enumerate(User.query.all()):
        user.other_description = descriptions[indizes[idx]]
        db_session.merge(user)

    db_session.commit()


def random_derangement(n):
    while True:
        v = range(n)
        for j in range(n - 1, -1, -1):
            p = random.randint(0, j)
            if v[p] == j:
                break
            else:
                v[j], v[p] = v[p], v[j]
        else:
            if v[0] != 0:
                return tuple(v)


def stats():
    for user in User.query.all():
        print "EMail:" + user.email
        print "Description: " + str(user.description)
        print "ODescription: " + str(user.other_description)
        print "\n"


# If this is called via python db_handler.py setup the db
if __name__ == "__main__":
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()

    args = sys.argv
    success = False
    if len(args) > 1:
        if sys.argv[1] == 'init':
            init_db()
            success = True
            print 'Successfully initialized'
        elif args[1] == 'shuffle':
            shuffle()
            success = True
            print 'Successfully initialized'
        elif args[1] == 'stats':
            stats()
            print len(User.query.all())

    if not success:
        print """Please type 'init' to (re)initialize the database or 'shuffle' to shuffle the descriptions."""
