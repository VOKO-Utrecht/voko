FROM python:3.7-alpine3.9

RUN addgroup -g 1000 -S app && adduser -u 1000 -S app -G app

RUN pip3 install pipenv

WORKDIR /app
RUN chown app:app /app

RUN apk update && apk add postgresql-dev gcc musl-dev python3-dev build-base linux-headers pcre-dev

USER app

COPY --chown=app:app ["requirements", "/app/"]

RUN pip install --user --upgrade pip
# Install dev packages too, for now
RUN pip install --user -r development.txt

RUN pip install --user -r production.txt

COPY --chown=app:app ["entrypoint.sh", "webapp", "/app/"]

EXPOSE 8000/tcp
ENTRYPOINT ["./entrypoint.sh"]
