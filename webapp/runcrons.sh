#!/bin/bash


cd /home/voko/voko

pipenv run python webapp/manage.py runcrons --settings=vokoa.settings.production 
