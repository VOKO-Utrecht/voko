#!/bin/bash


cd /home/voko/voko

uv run python webapp/manage.py runcrons --settings=vokou.settings.production 
