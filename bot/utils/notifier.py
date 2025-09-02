import smtplib, os
from email.mime.text import MIMEText

def send_email(subject, body):
    sender = os.getenv('GMAIL_FROM'); to = os.getenv('GMAIL_TO')
    app_pw = os.getenv('GMAIL_APP_PASSWORD')
    if not (sender and to and app_pw):
        return False
    msg = MIMEText(body)
    msg['Subject']=subject; msg['From']=sender; msg['To']=to
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as s:
        s.login(sender, app_pw)
        s.sendmail(sender, [to], msg.as_string())
    return True