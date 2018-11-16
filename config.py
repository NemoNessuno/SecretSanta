import yaml
import os

# Read secret config file
parent_dir = os.path.split(os.path.realpath(__file__))[0]
config = yaml.load(open('{}/{}'.format(parent_dir, 'secret_config')))

WTF_CSRF_ENABLED = True
SECRET_KEY = config['SECRET_KEY']

# -*- coding: utf-8 -*-
# ...
# available languages
LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch'
}

images = ['png', 'jpg', 'jpeg', 'gif']
sounds = ['mp3', 'wav', 'mkv', 'midi', 'ogg']
ALLOWED_EXTENSIONS = set(images + sounds)
UPLOAD_FOLDER = '/srv/www'

# Mail
MAIL_SERVER = config['MAIL_SERVER'].strip()
MAIL_PORT = config['MAIL_PORT']
MAIL_USE_TLS = config['MAIL_USE_TLS']
MAIL_USE_SSL = config['MAIL_USE_SSL']
MAIL_USERNAME = config['MAIL_USERNAME'].strip()
MAIL_PASSWORD = config['MAIL_PASSWORD'].strip()
