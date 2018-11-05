#!/bin/bash

#Always put the current path here or you won't be able to run!
export FLASK_CONFIG="/home/nemonessuno/Dropbox/Projekte/SecretSanta/config.py"
export FLASK_APP=main.py

pipenv run gunicorn -w 4 -b 0.0.0.0:5000 main:app
