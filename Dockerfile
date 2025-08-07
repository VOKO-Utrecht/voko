# Pull base image
# not using "slim" image, because UWSGI dependency fails
FROM python:3.12-bookworm as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV TZ="Europe/Amsterdam"

# Install system dependencies including PostgreSQL client and timezone data
RUN apt-get update && apt-get install -y \
    postgresql-client \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Configure timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime && echo Europe/Amsterdam > /etc/timezone

# Install uv
RUN pip install uv

# Set work directory
WORKDIR /code

# Copy dependencies & files
COPY ./pyproject.toml /code/

ARG CACHEBUST=1
# Recreate lock file
RUN uv lock
# Install dependencies
RUN uv sync --dev

# Install application into container
COPY . .

RUN ["chmod", "+x", "/code/docker-entrypoint.sh"]
ENTRYPOINT [ "/code/docker-entrypoint.sh" ]
