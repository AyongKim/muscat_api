import io
import base64
import six
import logging
import requests
from queue import Queue
from typing import List

from datetime import datetime, timedelta

from email.message import EmailMessage
from smtplib import SMTP_SSL
import jwt
from twilio.rest import Client

from flaskapp import db_utils
from flaskapp.constants import *
from flaskapp.enums import *

def check_key_exists_in_data(data: dict, keys: list):
    for key in keys:
        if key not in data:
            return FailResponse.missed_key_exception(key=key, data=data)
    return SUCCESS_RESPONSE

def check_value_in_data_is_not_null(data: dict, keys: list):
    for key in keys:
        if not data[key]:
            return FailResponse.missed_value_exception(key=key, data=data)
    return SUCCESS_RESPONSE

def check_key_value_in_data_is_validate(data: dict, keys: list):
    key_check_response = check_key_exists_in_data(data, keys)
    if key_check_response['result'] == FAIL_VALUE:
        return key_check_response

    #value_check_response = check_value_in_data_is_not_null(data, keys)
    #if value_check_response['result'] == FAIL_VALUE:
    #    return value_check_response
    return SUCCESS_RESPONSE

def send_mail(recipients, title, message):
    # 템플릿 생성
    msg = EmailMessage()
    # 보내는 사람 / 받는 사람 / 제목 입력
    msg["From"] = 'admin@muscat.co.kr'
    msg["To"] = recipients
    msg["Subject"] = title
    # 본문 구성
    msg.set_content(message)

    # 파일 첨부
    # with SMTP_SSL("smtp.gmail.com", 465) as smtp:
    #     smtp.login('muscat.check@gmail.com', 'wdgtwldgclgdlroc')
    #     smtp.send_message(msg, from_addr='admin@muscat.co.kr')
