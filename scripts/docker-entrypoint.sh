#!/bin/bash

flask db upgrade

gunicorn  app.wsgi:app --config gunicorn_conf.py
