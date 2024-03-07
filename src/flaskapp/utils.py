import io
import base64
import six
import logging
import requests
from queue import Queue
from typing import List

from datetime import datetime, timedelta

import jwt
from twilio.rest import Client

from flaskapp import db_utils
from flaskapp.constants import *
from flaskapp.enums import FailResponse


def issue_jwt_token(uid=None, user_info=None):
    if not user_info:
        if not uid:
            raise Exception('uid or user_info should be input')
        user_info_ob = db_utils.User.from_uid(uid)
        user_info = {'uid': uid, 'user_type': user_info_ob.user_type, 'nickname': user_info_ob.nickname}

    issue_time = datetime.utcnow()
    expire_time = issue_time + timedelta(minutes=JWT_TOKEN_EXPIRE_TIME_IN_MINUTE)
    next_expire_time = issue_time + timedelta(minutes=2 * JWT_TOKEN_EXPIRE_TIME_IN_MINUTE)

    payload = {'user': user_info,
               'iat': issue_time,
               'nbf': issue_time,
               'exp': expire_time}
    refresh_token_payload = {'user': user_info,
                             'iat': issue_time,
                             'nbf': expire_time,
                             'exp': next_expire_time}

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    db_utils.insert_login_token(token, refresh_token, issue_time.strftime('%Y-%m-%d %H:%M'))
    return token


def reissue_jwt_token(refresh_token, refresh_token_payload=None):
    if not refresh_token_payload:
        refresh_token_payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
    refresh_token_nbf = datetime.fromtimestamp(refresh_token_payload['nbf'])
    refresh_token_exp = datetime.fromtimestamp(refresh_token_payload['exp'])

    new_refresh_token_payload = {'user': refresh_token_payload['user'],
                                 'iat': datetime.utcnow(),
                                 'nbf': refresh_token_exp,
                                 'exp': refresh_token_exp + timedelta(minutes=JWT_TOKEN_EXPIRE_TIME_IN_MINUTE)}
    new_refresh_token = jwt.encode(new_refresh_token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    db_utils.insert_login_token(login_token=refresh_token, refresh_token=new_refresh_token,
                                nbf_time=refresh_token_nbf.strftime('%Y-%m-%d %H:%M'))


def decode_jwt_token(token):
    try:
        token_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
        return {'result': SUCCESS_VALUE, 'user': token_payload['user']}
    except Exception as e:
        if type(e) == jwt.ExpiredSignatureError:
            refresh_token = db_utils.get_refresh_token(token)
            db_utils.delete_login_token(token)
            if not refresh_token:
                return {'result': FAIL_VALUE, 'reason': e.args[0]}

            try:
                refresh_token_payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
                reissue_jwt_token(refresh_token=refresh_token, refresh_token_payload=refresh_token_payload)
            except Exception as e2:
                if type(e2) == jwt.ExpiredSignatureError:
                    refresh_token_payload = jwt.decode(
                        refresh_token, JWT_SECRET_KEY, algorithms=JWT_ALGORITHM, options={"verify_signature": False})
                    refresh_token = issue_jwt_token(user_info=refresh_token_payload['user'])

            return {'result': FAIL_VALUE, 'reason': 'refresh_token', 'refresh_token': refresh_token}
        else:
            return {'result': FAIL_VALUE, 'reason': e.args[0]}


def build_login_response(user):
    uid = user.uid
    user_type = user.user_type
    user_info = {'uid': uid, 'user_type': user_type, 'nickname': user.nickname}

    response = {'user': user_info}

    if user_type not in ['3', '4']:
        # 현재는 teacher, academy 는 로그인 인증이 필요없으므로 token 발행 제외
        jwt_token = issue_jwt_token(user_info=user_info)
        response['jwt_token'] = jwt_token

    return response


def get_paired_parents_info_of_student(student_id):
    parents_info = []

    parent_results = db_utils.get_parents_info_of_student(student_id=student_id)
    for parent_result in parent_results:
        parent = db_utils.User.from_db_result(parent_result)
        parents_info.append({'uid': parent.uid, 'name': parent.name})

    return parents_info


def validate_sns_register_info(user_data):
    if PROVIDER not in user_data:
        return FailResponse.missed_key_exception(PROVIDER, user_data)
    if PROVIDER_ID not in user_data:
        return FailResponse.missed_key_exception(PROVIDER_ID, user_data)

    provider = user_data[PROVIDER]
    provider_id = user_data[PROVIDER_ID]

    user_info = db_utils.get_user_info_by_provider(provider, provider_id)
    if user_info:
        return FailResponse.REGISTERED_USER
    return SUCCESS_RESPONSE


def validate_self_register_info(user_data):
    if EMAIL not in user_data:
        return FailResponse.missed_key_exception(EMAIL, user_data)

    e_mail = user_data.get(EMAIL)
    user_info = db_utils.get_user_info_by_email(e_mail)
    if user_info:
        return FailResponse.REGISTERED_USER
    return SUCCESS_RESPONSE


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

    value_check_response = check_value_in_data_is_not_null(data, keys)
    if value_check_response['result'] == FAIL_VALUE:
        return value_check_response
    return SUCCESS_RESPONSE


def search_school_open_api(search_conditions: dict):
    """
    https://open.neis.go.kr/portal/data/service/selectServicePage.do?page=1&rows=10&sortColumn=&sortDirection=&infId=OPEN17020190531110010104913&infSeq=2
    """
    school_open_api_base_url = f'{SCHOOL_OPEN_API_ENDPOINT}?Type=json&KEY={SCHOOL_OPEN_API_KEY}'
    for k, v in search_conditions.items():
        school_open_api_base_url += f'&{k}={v}'

    page_idx = 1

    while True:
        school_open_api_url = f'{school_open_api_base_url}&pIndex={page_idx}'

        response = requests.get(school_open_api_url)
        response.raise_for_status()

        returned_result_count = 0
        result = []

        api_result = response.json()
        if 'schoolInfo' in api_result:
            school_info_result = api_result['schoolInfo']
            for info in school_info_result:
                if 'head' in info:
                    for head_info in info['head']:
                        if 'list_total_count' in head_info:
                            returned_result_count = head_info['list_total_count']

                else:
                    logging.info('"head" info is not in result')

            for info in school_info_result:
                if 'row' in info:
                    result += info['row']

            if returned_result_count < 100:
                break
            page_idx += 1

        else:
            result_code = api_result['RESULT']['CODE']
            if result_code != 'INFO-000':
                logging.error(f'Request School OpenApi fails with error code {result_code} : '
                              f'{api_result["RESULT"]["MESSAGE"]}')
                return FAIL_RESPONSE

    return dict({'data': result}, **SUCCESS_RESPONSE)


def build_response_from_es_result(es_result):
    if es_result['result'] == SUCCESS_VALUE:
        return es_result
    else:
        return FailResponse.from_exception(exception_source='elasticsearch', exception=es_result['error'])


def send_sms_twilio(phone_number: str, code: str):
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    if phone_number.startswith('0'):
        phone_number = phone_number[1:]

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f'올클래스 인증 코드 입니다\n\n{code}',
        from_=TWILIO_PHONE_NUMBER,
        to=f'+82{phone_number}'
    )
    logging.info(f'Twilio message id : {message}')
    return SUCCESS_VALUE


def sorting_sort_values(sort: List, sort_conditions: List):
    result = []
    sort_queue = Queue()
    for s in sort:
        sort_queue.put(s)

    def is_float(el):
        try:
            float_el = float(el)
            return el == str(float_el)
        except ValueError:
            return False

    def is_int(el):
        try:
            int_el = int(el)
            return True
        except ValueError:
            return False

    for sort_condition in sort_conditions:
        if sort_condition == '_score':
            for _ in range(len(sort_queue.queue)):
                s = sort_queue.get()
                if is_float(s):
                    result.append(s)
                    break
                sort_queue.put(s)

        elif sort_condition == 'class_count':
            for _ in range(len(sort_queue.queue)):
                s = sort_queue.get()
                if is_int(s):
                    result.append(s)
                    break
                sort_queue.put(s)

        elif sort_condition == '_id':
            if len(sort_queue.queue) == 1:
                result.append(sort_queue.get())
            else:
                raise Exception(f'_id condition should be the last condition but there are still other conditions : '
                                f'{sort_queue}')

        else:
            raise Exception(f'{sort_condition} is wrong sort condition')

    return result


def decode_base64_file(data):
    """
    Fuction to convert base 64 to readable IO bytes and auto-generate file name with extension
    :param data: base64 file input
    :return: tuple containing IO bytes file and filename
    """
    # Check if this is a base64 string
    if isinstance(data, six.string_types):
        # Check if the base64 string is in the "data:" format
        if 'data:' in data and ';base64,' in data:
            # Break out the header from the base64 content
            header, data = data.split(';base64,')

        # Try to decode the file. Return validation error if it fails.
        try:
            decoded_file = base64.b64decode(data)
        except TypeError:
            TypeError('invalid_image')
            return FAIL_RESPONSE

        return io.BytesIO(decoded_file)


def upload_academy_profile_image(base64_file, academy_id):
    file = decode_base64_file(base64_file)
    s3_upload_object(file=file, path=f'academy/{academy_id}', bucket=S3_BUCKET)


def upload_user_profile_image(base64_file, uid, profile_numbering):
    file = decode_base64_file(base64_file)
    s3_upload_object(file=file, path=f'user/{uid}={profile_numbering}', bucket=S3_BUCKET)


def upload_academy_notice_base64_image(notice_dir, base64_file, file_name):
    file = decode_base64_file(base64_file)
    s3_upload_object(file=file, path=f'{notice_dir}/{file_name}', bucket=S3_BUCKET)


def upload_advertisement_base64_image(advertisement_dir, base64_file, file_name):
    file = decode_base64_file(base64_file)
    s3_upload_object(file=file, path=f'{advertisement_dir}/{file_name}', bucket=S3_BUCKET)


def s3_upload_object(file, path, bucket):
    client = boto3.client('s3', region_name='ap-northeast-2')
    client.upload_fileobj(
        file,
        bucket,
        path
    )
    return
