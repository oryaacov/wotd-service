import requests
import re
import smtplib
import os
from logger import Logger, LoggerConfig

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0',
}

data = {
    'language': 'Hebrew',
    'date': '',
    'affiliate_id': 'undefined',
}

logger = Logger("wotd", LoggerConfig(file_path="./logs/wotd.log", max_log_file_size_mb=10, min_log_level="trace"))

def get_wotd():
    response = requests.post('https://www.innovativelanguage.com/widgets/wotd/small.php', headers=headers, data=data)
    if response.status_code != 200:
        print(f'failed to get response with {response.status_code} {response.text}')
        exit(1)
        
    wotd_regex = re.compile(r"(?:wotd-widget-sentence-main-space-text[^>]*>(?P<hebrew>[^<]*)).*(?:wotd-widget-sentence-quizmode-space-text big romanization[^>]*>(?P<hebrish>[^<]*)).*(?:wotd-widget-sentence-quizmode-space-text big english[^>]*>(?P<english>[^<]*)).*(?:wotd-widget-sentence-quizmode-space-text noun[^>]*>(?P<noun>[^<]*))")
    html = response.text.replace('\r', '').replace('\n', '')
    res = re.search(wotd_regex, html)
    return res.groupdict()


def build_email_content(wotd):
    return f'\nHey cute being\nHere is your hebrew word of the day:\n\n\nHebrew: {wotd["hebrew"]}\nHebrish: {wotd["hebrish"]}\nEnglish: {wotd["english"]}\nNoun: {wotd["noun"]}\n\nWith a lot of love,\nOr Yaacov'


def send_email(msg, addresses):
    from_email_address = os.environ["WOTD_EMAIL_ADDRESS"]
    password = os.environ["WOTD_EMAIL_PASSWORD"]
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.ehlo()
    server.starttls()
    server.login(from_email_address, password)
    for address in addresses:
        server.sendmail(from_email_address, address, msg.encode('utf-8'))
    
    server.close()


def main():
    try:
        logger.info("cute being log of the day script starting")
        wotd = get_wotd()

        logger.info(f"word od the day {wotd}")
        mail_content = build_email_content(wotd)

        logger.debug(f"message body {mail_content}")
        send_email(mail_content, [os.environ["WOTD_RECIVERS"].split(';')])

        logger.debug(f"wotd sent, done")
    except Exception as err:
        logger.error("failed to send word of the day", err)

main()
