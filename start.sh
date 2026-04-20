#!/usr/bin/env bash

echo "Starting app..."

export FLASK_APP=app.py
export FLASK_ENV=production

python app.py