# Pull base image
# not using "slim" image, because UWSGI dependency fails
FROM python:3.8-bullseye as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

# Install pipenv
RUN pip install pipenv

# Set work directory
WORKDIR /code

# Copy dependencies & files
COPY ./Pipfile /code/
# Recreate lock file
RUN pipenv lock
# Install dependencies
RUN pipenv install --dev

# Install application into container
COPY . .

RUN ["chmod", "+x", "/code/docker-entrypoint.sh"]
ENTRYPOINT [ "/code/docker-entrypoint.sh" ]
