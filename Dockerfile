FROM python:3.11.3

WORKDIR /app/
# Install Chrome WebDriver

RUN apt-get update -y && apt-get install -y chromium

# CHROMIUM default flags for container environnement
# The --no-sandbox flag is needed by default since we execute chromium in a root environnement
RUN echo 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --no-sandbox"' >> /etc/chromium.d/default-flags

RUN apt-get install -y gcc
RUN apt-get install -y libpq-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD database blood-bowl-league-manager/database
ADD server blood-bowl-league-manager/server
ADD table blood-bowl-league-manager/table
ADD util blood-bowl-league-manager/util

COPY *.py blood-bowl-league-manager/

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /

VOLUME /app/blood-bowl-league-manager/instance
VOLUME /app/blood-bowl-league-manager/data
VOLUME /app/blood-bowl-league-manager/server/static/output

EXPOSE 80

WORKDIR /app/blood-bowl-league-manager

CMD ["python", "-m", "waitress","--port=80","main:app"]
