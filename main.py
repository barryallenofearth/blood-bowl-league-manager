import logging
import logging.handlers
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from server.server import app


def setup_log(log_level: int):
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%d-%b-%y %H:%M:%S')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    if not os.path.exists("log"):
        os.mkdir("log")
    file_log_handler = logging.handlers.RotatingFileHandler(f'log/paypal_donation_mail_scraper.log', backupCount=3, encoding="utf-8")
    file_log_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    logger.addHandler(file_log_handler)
    logger.addHandler(console_handler)

    logging.info("Log setup complete")

    scheduler = BackgroundScheduler()
    scheduler.add_job(file_log_handler.doRollover, trigger='cron', hour='0')
    scheduler.start()


setup_log(logging.INFO)

if __name__ == "__main__":
    logging.info("Starting server")
    app.run(host="0.0.0.0", port=443, ssl_context=("certificates/cert.pem", "certificates/key.pem"))
