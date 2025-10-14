#!/bin/bash


cd /home/voko/voko

uv run --env-file .env python webapp/manage.py runcrons --settings=vokou.settings.production 
