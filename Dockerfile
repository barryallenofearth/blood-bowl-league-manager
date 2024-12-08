FROM python:3.11-slim

WORKDIR /app/

RUN apt-get update -y

RUN apt-get install -y gcc
RUN apt-get install -y libpq-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD database blood-bowl-league-manager/database
ADD server blood-bowl-league-manager/server
ADD table blood-bowl-league-manager/table
ADD util blood-bowl-league-manager/util

COPY *.py blood-bowl-league-manager/

ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV PYTHONUNBUFFERED=1

WORKDIR /

VOLUME /app/blood-bowl-league-manager/certificates
VOLUME /app/blood-bowl-league-manager/instance
VOLUME /app/blood-bowl-league-manager/data
VOLUME /app/blood-bowl-league-manager/server/static/logos

EXPOSE 80

WORKDIR /app/blood-bowl-league-manager

ENV SCRIPT_NAME=/blood-bowl
RUN sed -i "s+/static/css/Nuffle.ttf+$SCRIPT_NAME/static/css/Nuffle.ttf+g" /app/blood-bowl-league-manager/server/static/css/styles.css
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:80", "main:app"]
