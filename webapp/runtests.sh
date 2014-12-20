#!/bin/bash
watch -n 1 -- python manage.py test --settings=vokou.settings.testing
