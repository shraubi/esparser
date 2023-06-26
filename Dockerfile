FROM python:3.9-slim
RUN apt-get update && apt-get install -y gnupg wget curl cron unzip && python3 -m pip install --upgrade pip

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
RUN CHROME_VERSION=$(google-chrome --version | awk '{ print $3 }' | sed 's/\..*//') \
    && CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION) \
    && wget -q --no-check-certificate -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /app/ \
    && rm /tmp/chromedriver.zip

WORKDIR /app
RUN touch /app/cron.log
ADD requirements.txt /app
RUN apt-get install unzip && apt install curl -y
RUN pip install -r requirements.txt 

ENV UPWORK_USERNAME="doesnotmatterkate@gmail.com"
ENV UPWORK_PASS="Uu4YpyPhhCtZbZR"
ENV TG_BOT_RECEIVERS="406962410,793022435,240372740,5592590203,85537963,191591177"
ENV UPWORK_IMPORTANT_BOT_TOKEN=5588913168:AAFcfMIzx82ZABMvKbWyqIauclG9E7A-kyE
ENV UPWORK_ALLPYTHON_BOT_TOKEN=5510978330:AAGcrTNnlTMnyFA8baKbbQMy80FGNPzOtiU
ENV DB_CONN=postgresql://postgres:uparser123@uparser.cdwuxqsxjd0r.eu-central-1.rds.amazonaws.com:5432
ENV PYTHONPATH="${PYTHONPATH}:/opt/:/app/:"

ADD run.sh /app/
ADD .env /app/
ADD cron /etc/cron.d/cron
RUN chmod 0644 /etc/cron.d/cron
RUN chmod 0744 /app/run.sh
RUN crontab /etc/cron.d/cron
ADD scrapers/upwork.py /app/scrapers/upwork.py

CMD ["cron", "-f"]