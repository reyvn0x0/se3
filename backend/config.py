import os

class Config:

    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'uni_timetable.db')}"

    
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'