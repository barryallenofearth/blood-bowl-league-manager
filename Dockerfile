FROM python:3.11.3

WORKDIR /app/
# Install Chrome WebDriver

RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    mkdir -p /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    curl -sS -o /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip -qq /tmp/chromedriver_linux64.zip -d /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver && \
    ln -fs /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver /usr/local/bin/chromedriver

# Install Google Chrome
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -yqq update && \
    apt-get -yqq install google-chrome-stable && \
    rm -rf /var/lib/apt/lists/* \

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD database blood-bowl-leauge-manager/database
ADD server blood-bowl-leauge-manager/server
ADD table blood-bowl-leauge-manager/table
ADD util blood-bowl-leauge-manager/util

COPY *.py blood-bowl-leauge-manager/

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /

VOLUME /app/blood-bowl-leauge-manager/instance
VOLUME /app/blood-bowl-leauge-manager/data

EXPOSE 80

WORKDIR /app/blood-bowl-leauge-manager

CMD ["python", "-m", "waitress","--port=80","main:app"]
