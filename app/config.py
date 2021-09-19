import os
import json


class BaseConfig(object):
    """Base config class"""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SECRET_KEY = 'AasHy7I8484K8I32seu7nni8YHHu6786gi'
    TIMEZONE = "UTC"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    DATE_FORMAT = "%d %B %Y"
    MONTH_FORMAT = "%B %Y"
    ZONE_FORMAT = "%z"
    MEDIA_URL = "app/media"
    UPLOAD_DIR = f"{BASE_DIR}/app/media/uploads"
    TMP_DIR = f"{BASE_DIR}/app/media/tmp"
    GENERATED_DIR = f"{BASE_DIR}/app/media/generated"
    # email
    MAIL_SERVER='smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'amobitinfo@gmail.com'
    MAIL_PASSWORD = '@_AmoBit2020'
    MAIL_PASSWORD = 'wnocbulgkiatkucc'
    MAIL_DEFAULT_SENDER = 'amobitifo@gmail.com'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_SUPPRESS_SEND = False
    

class ProductionConfig(BaseConfig):
    """Production specific config"""
    DEBUG = False
    TESTING = False
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///models/database.db'


class DevelopmentConfig(BaseConfig):
    """Development environment specific config"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///models/database.db'



