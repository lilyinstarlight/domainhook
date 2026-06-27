import smtplib

import email.mime.multipart
import email.mime.text

from domainhook import config


def send_dnssec(domain, dnssec_data):
    send(config.dnssec_subject.format(domain=domain, **dnssec_data), config.dnssec_message.format(domain=domain, **dnssec_data))


def send_failure(domain, action, message):
    send(config.failure_subject.format(domain=domain, action=action, message=message), config.failure_message.format(domain=domain, action=action, message=message))


def send(subject, message):
    msg = email.mime.multipart.MIMEMultipart()

    msg['Subject'] = subject
    msg['From'] = config.sender
    msg['To'] = config.recipient

    msg.attach(email.mime.text.MIMEText(message))

    if config.smtp_tls == 'tls':
        SMTP = smtplib.SMTP_SSL
    else:
        SMTP = smtplib.SMTP

    with SMTP(config.smtp_host, config.smtp_port) as s:
        if config.smtp_tls == 'starttls':
            s.starttls()
        if config.smtp_user:
            s.login(config.smtp_user, config.smtp_password)
        s.send_message(msg)
        s.quit()
