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

ARG CACHEBUST=1
# Recreate lock file
RUN pipenv lock && pipenv install --dev

# Install application into container
COPY . .

EXPOSE 8000
RUN ["chmod", "+x", "/code/docker-entrypoint.sh"]
ENTRYPOINT [ "/code/docker-entrypoint.sh" ]
