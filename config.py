WTF_CSRF_ENABLED = True
SECRET_KEY = 'SecretSantaSecretPassPhrase'

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
