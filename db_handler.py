import pyclbr
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
    import models
    from sqlalchemy import Table

    for class_name in pyclbr.readmodule(models.__name__).keys():
        try:
            table_class = getattr(sys.modules[models.__name__], class_name)
            if not table_class.__table__.exists(bind=engine):
                table_class.__table__.create(bind=engine)
                db_session.commit()
        except AttributeError:
            pass

    for table_object in [class_object for class_object in models.__dict__.values() if type(class_object) == Table]:
        try:
            if not table_object.exists(bind=engine):
                table_object.create(bind=engine)
                db_session.commit()
        except AttributeError:
            pass


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
