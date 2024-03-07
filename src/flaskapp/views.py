import copy
import logging
import random
import string
import uuid
import requests
from datetime import datetime
from pytz import timezone
from werkzeug.exceptions import BadRequest

from flask import request, g
from flask_restx import Resource
from pymysql.err import Error
from twilio.rest import TwilioException

from flaskapp import app
from flaskapp import utils
from flaskapp import db_utils
from flaskapp import es_utils
from flaskapp import schedule
from flaskapp.schedule import Scheduler
from flaskapp.flask_namespaces import *
from flaskapp.constants import *
from flaskapp.enums import UserCode, FailResponse


def require_auth(meth):
    e = BadRequest()
    method = meth.__name__
    if method in ("get", "post", "put", "delete"):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
            except IndexError:
                e.data = FailResponse.invalid_token_exception(
                    'Authorization jwt token format: It should be "Bearer JWT_TOKEN"')
                raise e
        else:
            e.data = FailResponse.missed_key_exception(key='Authorization', data='Header')
            raise e

        if auth_token:
            refresh_token = db_utils.get_refresh_token(auth_token)
            if not refresh_token:
                # token 이 db 에 없을 경우
                e.data = FailResponse.invalid_token_exception('token is not in DB')
                raise e

            result = utils.decode_jwt_token(auth_token)
            if result['result'] == FAIL_VALUE:
                if result['reason'] == 'refresh_token':
                    # token 이 만료되서 새로운 token 전달
                    e.data = result
                else:
                    e.data = FailResponse.invalid_token_exception(result['reason'])
                raise e

            uid_in_token = result['user']['uid']

            uid_in_request = None
            if method != 'get':
                content_type = request.mimetype
                if content_type in ['multipart/form-data', 'application/x-www-form-urlencoded']:
                    uid_in_request = request.form.to_dict().get('uid', None)

                elif content_type == 'application/json':
                    if 'uid' in request.json:
                        uid_in_request = request.json['uid']

            if (method == 'get') and ('uid' in request.args):
                uid_in_request = request.args['uid']

            if uid_in_request and (uid_in_request != uid_in_token):
                # token 내 uid 랑 body 내의 uid 가 다를 경우
                e.data = FailResponse.invalid_token_exception('Uid from jwt token and body are different')
                raise e
    return meth


def validation_limiter(methods, validator):
    methods = [name.lower() for name in methods]

    def inner(meth):
        if meth.__name__ not in methods:
            return meth
        return validator(meth)

    return inner


class LoginAuthResource(Resource):
    method_decorators = [
        validation_limiter(["GET", "POST", "PUT", "DELETE"], require_auth)
    ]


def build_login_success_response(uid):
    user = db_utils.User.from_uid(uid)
    response = utils.build_login_response(user)
    return dict(response, **SUCCESS_RESPONSE)


@app.before_request
def log_request_info():
    method = request.method.upper()
    url = request.full_path

    request_data = ''
    content_type = request.mimetype
    if content_type in ['multipart/form-data', 'application/x-www-form-urlencoded']:
        request_data = copy.deepcopy(request.form.to_dict())
    elif content_type == 'application/json':
        request_data = copy.deepcopy(request.json)

    if 'img_url' in request_data:
        del request_data['img_url']

    app.logger.info(f"{method} {url}  {content_type}  {request_data}")


@app.errorhandler(Exception)
def handle_exception(e):
    uid_term = ''
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
        result = utils.decode_jwt_token(auth_token)
        uid_term = f"(uid : {result['user']['uid']})"

    # pass through HTTP errors
    error_msg = BadRequest()

    if isinstance(e, Error):
        app.logger.error(f'{uid_term} MySQL exception : {e}')
        error_msg.data = FailResponse.from_exception('MySQL DB', e)
        raise error_msg

    if isinstance(e, TwilioException):
        app.logger.error(f'{uid_term} Twilio exception : {e}')
        error_msg.data = FailResponse.from_exception('Twilio', e)
        raise error_msg

    app.logger.error(f'{uid_term} {e}')


@app.teardown_appcontext
def teardown_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return 'index'


@app.route('/term_of_service')
def term_of_service():
    response = requests.get(url=f'{CLOUD_FRONT_URL}/term_of_service.txt')
    response.raise_for_status()
    return dict({'data': response.content.decode('utf-8')})


@app.route('/personal_data_policy')
def personal_data_policy():
    response = requests.get(url=f'{CLOUD_FRONT_URL}/personal_data_policy.txt')
    response.raise_for_status()
    return dict({'data': response.content.decode('utf-8')})


@app.route('/youth_protection_policy')
def youth_protection_policy():
    response = requests.get(url=f'{CLOUD_FRONT_URL}/youth_protection_policy.txt')
    response.raise_for_status()
    return dict({'data': response.content.decode('utf-8')})


# ----- UserNs -----
@UserNs.route('')
@require_auth
@UserNs.doc(params=AUTHORIZATION_HEADER)
class UserAPI(LoginAuthResource):
    @UserNs.expect(update_user_info_model)
    def put(self):
        """업데이트 user info"""
        user_data: dict = request.form.to_dict()
        uid = user_data.pop('uid')
        result = db_utils.update_user_info(uid=uid, **user_data)
        return result

    @UserNs.expect(delete_user_model)
    def delete(self):
        """회원 탈퇴"""
        auth_header = request.headers.get('Authorization')
        auth_token = auth_header.split(" ")[1]

        user_data = request.form.to_dict()
        uid = user_data['uid']

        db_utils.hard_delete_user(uid)
        db_utils.delete_login_token(auth_token)
        return SUCCESS_RESPONSE


@UserNs.route('/phone_number/send_code')
class SendCodePhoneNumber(Resource):
    @UserNs.expect(send_code_phone_number_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """휴대폰 번호 인증을 위한 코드 발송"""
        phone_number_dict: dict = request.form.to_dict()
        phone_number: str = phone_number_dict['phone_number']
        phone_number.replace('-', '').replace(' ', '')

        user_result = db_utils.get_user_info_by_phone_number(phone_number)
        if user_result:
            return FailResponse.REGISTERED_USER

        verify_code = str(random.randint(100000, 999999))
        utils.send_sms_twilio(phone_number=phone_number, code=verify_code)
        db_utils.save_code_for_verifying_phone_number(phone_number=phone_number, code=verify_code, purpose='phone')
        return SUCCESS_RESPONSE


@UserNs.route('/phone_number/verify_code')
class VerifyCodePhoneNumber(Resource):
    @UserNs.expect(verify_code_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """휴대폰 번호 코드 인증"""
        code_dict: dict = request.form.to_dict()
        code = code_dict['code']
        phone_number: str = code_dict['phone_number']
        phone_number.replace('-', '').replace(' ', '')
        result = db_utils.verify_code_for_phone_number(phone_number=phone_number, code=code, purpose='phone')
        return result


@UserNs.route('/forgot/email/send_code')
class SendCodeForgotEmail(Resource):
    @UserNs.expect(phone_number_model)
    def post(self):
        """email 찾기 위해 인증번호 발송"""
        phone_number_dict: dict = request.form.to_dict()
        phone_number: str = phone_number_dict['phone_number']
        phone_number.replace('-', '').replace(' ', '')

        user_info = db_utils.get_user_uid_and_email_by_phone_number(phone_number)
        if not user_info:
            return FailResponse.UNVERIFIED_PHONE_NUMBER

        verify_code = str(random.randint(100000, 999999))
        utils.send_sms_twilio(phone_number=phone_number, code=verify_code)
        db_utils.save_code_for_verifying_phone_number(phone_number=phone_number, code=verify_code, purpose='email')
        return SUCCESS_RESPONSE


@UserNs.route('/forgot/email/verify_code')
class VerifyCodeForgotEmail(Resource):
    @UserNs.expect(verify_code_model)
    @UserNs.response(200, SUCCESS_VALUE, email_info_model)
    def post(self):
        """email 찾기 인증번호 인증"""
        code_dict: dict = request.form.to_dict()
        code = code_dict['code']
        phone_number: str = code_dict['phone_number']
        phone_number.replace('-', '').replace(' ', '')

        result = db_utils.verify_code_for_phone_number(phone_number=phone_number, code=code, purpose='email')
        if result['result'] == SUCCESS_VALUE:
            user_info = db_utils.get_user_uid_and_email_by_phone_number(phone_number)
            result = dict({'email': user_info[1]}, **SUCCESS_RESPONSE)

        return result


@UserNs.route('/forgot/password/send_code')
class SendCodeForgotPassword(Resource):
    @UserNs.expect(forgot_password_send_code_model)
    def post(self):
        phone_number_dict: dict = request.form.to_dict()
        phone_number: str = phone_number_dict['phone_number']
        phone_number.replace('-', '').replace(' ', '')

        email = phone_number_dict['email']
        email_result = db_utils.get_user_info_by_email(email)
        if not email_result:
            return FailResponse.NOT_REGISTERED_USER

        user_info = db_utils.get_user_uid_and_email_by_phone_number(phone_number)
        if not user_info:
            return FailResponse.UNVERIFIED_PHONE_NUMBER

        if user_info[1] != email:
            return FailResponse.UNVERIFIED_PHONE_NUMBER

        verify_code = str(random.randint(100000, 999999))
        utils.send_sms_twilio(phone_number=phone_number, code=verify_code)
        db_utils.save_code_for_verifying_phone_number(phone_number=phone_number, code=verify_code, purpose='password')

        return SUCCESS_RESPONSE


@UserNs.route('/forgot/password/verify_code')
class VerifyCodeForgotPassword(Resource):
    @UserNs.expect(verify_code_model)
    @UserNs.response(200, SUCCESS_VALUE, email_info_model)
    def post(self):
        """email 찾기 인증번호 인증"""
        code_dict: dict = request.form.to_dict()
        code = code_dict['code']
        phone_number: str = code_dict['phone_number']
        phone_number.replace('-', '').replace(' ', '')

        result = db_utils.verify_code_for_phone_number(phone_number=phone_number, code=code, purpose='password')
        return result


@UserNs.route('/forgot/password/new_password')
class PutNewPassword(Resource):
    @UserNs.expect(forgot_password_new_password_model)
    def post(self):
        """새로운 password 주입"""
        passwd_dict: dict = request.form.to_dict()
        password = passwd_dict['password']
        phone_number: str = passwd_dict['phone_number']
        phone_number.replace('-', '').replace(' ', '')

        verify_number = db_utils.verify_password_change(phone_number)
        if verify_number:
            user_info = db_utils.get_user_uid_and_email_by_phone_number(phone_number)
            uid = user_info[0]

            db_utils.update_password_of_user(uid=uid, passwd=password, verify_number=verify_number)
            return SUCCESS_RESPONSE
        else:
            return FAIL_RESPONSE


@UserNs.route('/academy_info_agree')
class AcademyInfoAgree(LoginAuthResource):
    @UserNs.response(200, SUCCESS_VALUE, get_academy_info_agree_model)
    def get(self):
        """학원 정보 제공 동의 현황 조회"""
        auth_header = request.headers.get('Authorization')
        auth_token = auth_header.split(" ")[1]
        result = utils.decode_jwt_token(auth_token)
        uid = result['user']['uid']

        academy_info_agree = db_utils.get_academy_info_agree(uid)
        if academy_info_agree:
            return dict({'data': {'get_academy_info': academy_info_agree}}, **SUCCESS_RESPONSE)
        else:
            return FAIL_RESPONSE

    @UserNs.expect(update_academy_info_agree_model)
    def post(self):
        """학원 정보 제공 동의 수정"""
        agree_data: dict = request.form.to_dict()
        uid = agree_data['uid']
        get_academy_info = agree_data['get_academy_info']
        db_utils.save_academy_info_agree(uid=uid, get_academy_info=get_academy_info)
        return SUCCESS_RESPONSE


@UserNs.route('/register/sns/student')
class RegisterSnsStudentInfo(Resource):
    @UserNs.expect(sns_register_student_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    def post(self):
        """SNS login 학생 회원 가입"""
        user_data: dict = request.form.to_dict()

        response = utils.validate_sns_register_info(user_data=user_data)
        if response['result'] == FAIL_VALUE:
            return response

        user_type = user_data[USER_TYPE]
        if user_type == UserCode.STUDENT.value:
            essential_keys = [NICKNAME, PROVIDER, PROVIDER_ID]
            check_response = utils.check_key_value_in_data_is_validate(data=user_data, keys=essential_keys)
            if check_response['result'] == FAIL_VALUE:
                return check_response

            student_id = db_utils.register_student_user_sns(user_data)
            return build_login_success_response(student_id)
        else:
            return FailResponse.improper_user_type_exception(
                user_type=user_type, valid_user_types=[UserCode.STUDENT.value])


@UserNs.route('/register/sns/parent')
class RegisterSnsParentInfo(Resource):
    @UserNs.expect(sns_register_parent_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    def post(self):
        """SNS login 학부모 회원 가입"""
        user_data: dict = request.form.to_dict()

        response = utils.validate_sns_register_info(user_data=user_data)
        if response['result'] == FAIL_VALUE:
            return response

        user_type = user_data[USER_TYPE]
        if user_type == UserCode.PARENT.value:
            essential_keys = [NICKNAME, NAME, PROVIDER, PROVIDER_ID]
            check_response = utils.check_key_value_in_data_is_validate(data=user_data, keys=essential_keys)
            if check_response['result'] == FAIL_VALUE:
                return check_response

            parent_id = db_utils.register_parent_user_sns(user_data=user_data)
            return build_login_success_response(parent_id)
        else:
            return FailResponse.improper_user_type_exception(user_type=user_type,
                                                             valid_user_types=[UserCode.PARENT.value])


@UserNs.route('/register/self/student')
class RegisterSelfStudentInfo(Resource):
    @UserNs.expect(self_register_student_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """Self login 학생 회원 가입"""
        user_data: dict = request.form.to_dict()
        response = utils.validate_self_register_info(user_data=user_data)
        if response['result'] == FAIL_VALUE:
            return response

        user_type = user_data[USER_TYPE]
        if user_type == UserCode.STUDENT.value:
            essential_keys = [EMAIL, PASSWORD, NICKNAME, NAME, 'school_code']
            check_response = utils.check_key_value_in_data_is_validate(data=user_data, keys=essential_keys)
            if check_response['result'] == FAIL_VALUE:
                return check_response

            student_id = db_utils.register_student_user_self(user_data)
            return build_login_success_response(student_id)
        else:
            return FailResponse.improper_user_type_exception(
                user_type=user_type, valid_user_types=[UserCode.STUDENT.value])


@UserNs.route('/register/self/parent')
class RegisterSelfParentInfo(Resource):
    @UserNs.expect(self_register_parent_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """self login 학부모 회원 가입"""
        user_data: dict = request.form.to_dict()
        response = utils.validate_self_register_info(user_data=user_data)
        if response['result'] == FAIL_VALUE:
            return response

        user_type = user_data[USER_TYPE]
        if user_type == UserCode.PARENT.value:
            essential_keys = [EMAIL, PASSWORD, NICKNAME, NAME]
            check_response = utils.check_key_value_in_data_is_validate(data=user_data, keys=essential_keys)
            if check_response['result'] == FAIL_VALUE:
                return check_response

            parent_id = db_utils.register_parent_user_self(user_data=user_data)
            return build_login_success_response(parent_id)
        else:
            return FailResponse.improper_user_type_exception(user_type=user_type,
                                                             valid_user_types=[UserCode.PARENT.value])


@UserNs.route('/register/self/academy')
class RegisterSelfAcademyInfo(Resource):
    @UserNs.expect(self_register_academy_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """Self login ACADEMY 회원 가입"""
        user_data: dict = request.json
        response = utils.validate_self_register_info(user_data=user_data)
        if response['result'] == FAIL_VALUE:
            return response

        user_type = user_data[USER_TYPE]
        if user_type == UserCode.ACADEMY.value:
            essential_keys = [EMAIL, PASSWORD, NAME, PHONE_NUMBER, 'address_info']
            check_response = utils.check_key_value_in_data_is_validate(data=user_data, keys=essential_keys)
            if check_response['result'] == FAIL_VALUE:
                return check_response

            check_response = utils.check_key_exists_in_data(data=user_data, keys=[SUBJECT_INFO, 'homepage_url'])
            if check_response['result'] == FAIL_VALUE:
                return check_response

            for subject_info in user_data[SUBJECT_INFO]:
                subject_info_essential_keys = ['major_subject_name', 'major_subject_id', 'school_course']
                check_response = utils.check_key_value_in_data_is_validate(data=subject_info,
                                                                           keys=subject_info_essential_keys)
                if check_response['result'] == FAIL_VALUE:
                    return check_response

            academy_id = db_utils.register_academy_user_info_self(user_data)
            result = es_utils.insert_academy_info(academy_id=academy_id, academy_data=user_data)

            if 'img_url' in user_data:
                img_url = user_data['img_url']
                utils.upload_academy_profile_image(img_url, academy_id)

            if result['result'] == FAIL_VALUE:
                return result

            return build_login_success_response(academy_id)
        else:
            return FailResponse.improper_user_type_exception(user_type=user_type,
                                                             valid_user_types=[UserCode.ACADEMY.value])


@UserNs.route('/register/self/teacher')
class RegisterSelfTeacher(Resource):
    @UserNs.expect(self_register_teacher_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """Self login TEACHER 회원 가입"""
        user_data: dict = request.json
        response = utils.validate_self_register_info(user_data=user_data)
        if response['result'] == FAIL_VALUE:
            return response

        user_type = user_data[USER_TYPE]
        if user_type == UserCode.TEACHER.value:
            essential_keys = [EMAIL, PASSWORD, NAME, SUBJECT_INFO, PHONE_NUMBER, BIRTHDAY, GENDER]
            check_response = utils.check_key_value_in_data_is_validate(data=user_data, keys=essential_keys)
            if check_response['result'] == FAIL_VALUE:
                return check_response

            for subject_info in user_data[SUBJECT_INFO]:
                check_response = utils.check_key_value_in_data_is_validate(subject_info, SUBJECT_INFO_ESSENTIAL_KEYS)
                if check_response['result'] == FAIL_VALUE:
                    return check_response

            teacher_id = db_utils.register_teacher_user_info_self(user_data)
            es_utils.insert_teacher_info(teacher_id=teacher_id, teacher_data=user_data)
            return build_login_success_response(teacher_id)
        else:
            return FailResponse.improper_user_type_exception(user_type=user_type,
                                                             valid_user_types=[UserCode.TEACHER.value])


@UserNs.route('/pairing/token/issue')
@require_auth
class PairingTokenIssue(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.expect(uid_info_model)
    @UserNs.response(200, SUCCESS_VALUE, issue_token_output_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """Parent 의 새로운 token 발행 또는 기존 발행된 token 정보 조회"""
        data = request.form.to_dict()
        parent_id = data['uid']
        user = db_utils.User.from_uid(parent_id)

        user_type = user.user_type
        if user_type == UserCode.PARENT.value:
            result = db_utils.get_pairing_token_of_parent(parent_id)
            if result:
                logging.info(f'{user_type}#{parent_id} user already has issued token')
                token = result[0]
            else:
                # 학생 정보가 있을 때만 새로운 토큰 발행
                logging.info(f'Issue token for {user_type}#{parent_id} user')
                token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                db_utils.insert_pairing_token_of_parent(parent_id=parent_id, pairing_token=token)

            return dict({'token': token}, **SUCCESS_RESPONSE)
        else:
            return FailResponse.improper_user_type_exception(user_type=user_type,
                                                             valid_user_types=[UserCode.STUDENT.value])


@UserNs.route('/pairing/token/match')
@require_auth
class PairingTokenMatch(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.expect(match_token_model)
    @UserNs.response(200, SUCCESS_VALUE, success_response_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """학생이 token 으로 학부모의 매칭"""
        data = request.form.to_dict()
        student_id = data['uid']
        token = data['token']
        result = db_utils.match_pairing_token(student_id=student_id, pairing_token=token)
        return result


@UserNs.route('/pairing/select_student')
@require_auth
class PairingSelectStudeent(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.expect(select_paired_student_model)
    def post(self):
        """페어링 된 학생 switch"""
        data = request.form.to_dict()
        parent_id = data['uid']
        student_id = data['student_id']
        db_utils.select_paired_student(parent_id=parent_id, student_id=student_id)
        return SUCCESS_RESPONSE


@UserNs.route('/pairing/token')
@require_auth
class PairingDeleteToken(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.expect(match_token_model)
    def delete(self):
        """페어링 token 및 임시 학생 정보 삭제"""
        data = request.form.to_dict()
        parent_id = data['uid']
        token = data['token']
        db_utils.delete_token_and_temp_student_info(parent_id=parent_id, token=token)
        return SUCCESS_RESPONSE


@UserNs.route('/login/sns')
class LoginSnsUser(Resource):
    @UserNs.expect(sns_login_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    def post(self):
        """SNS login User 의 로그인 시 유저 정보 체크"""
        user_data: dict = request.form.to_dict()
        provider = user_data[PROVIDER]
        provider_id = user_data[PROVIDER_ID]

        user_result = db_utils.get_user_info_by_provider(provider, provider_id)
        if not user_result:
            return FailResponse.NOT_REGISTERED_USER
        user = db_utils.User.from_db_result(user_result)

        uid = user.uid
        active = user.active
        if active == 0:
            return FailResponse.INACTIVE_USER
        else:
            return build_login_success_response(uid)


@UserNs.route('/login/self')
class LoginSelfUser(Resource):
    @UserNs.expect(self_login_model)
    @UserNs.response(200, SUCCESS_VALUE, success_login_token_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """Self login User 의 로그인 시 유저 정보 체크"""
        user_data: dict = request.form.to_dict()
        email = user_data[EMAIL]
        passwd = user_data[PASSWORD]

        email_result = db_utils.get_user_info_by_email(email)
        if not email_result:
            return FailResponse.NOT_REGISTERED_USER

        password_result = db_utils.check_password(e_mail=email, passwd=passwd)
        if not password_result:
            return FailResponse.INVALID_PASSWORD
        else:
            uid = password_result[0]
            active = password_result[1]
            if active == 0:
                return FailResponse.INACTIVE_USER
            else:
                return build_login_success_response(uid)


@UserNs.route('/logout')
@require_auth
class LogoutUser(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    def get(self):
        """유저 로그아웃"""
        auth_header = request.headers.get('Authorization')
        auth_token = auth_header.split(" ")[1]
        db_utils.delete_login_token(auth_token)
        return SUCCESS_RESPONSE


@UserNs.route('/student/<uid>')
@require_auth
class UserStudent(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.response(200, SUCCESS_VALUE, student_user_info_model)
    def get(self, uid):
        """학생 정보 조회"""
        user = db_utils.User.from_uid(uid)
        user_result = user.to_dict()

        parents_info = utils.get_paired_parents_info_of_student(student_id=uid)
        user_result['pairing_info'] = {
            'is_paired': len(parents_info) != 0,
            'paired': parents_info
        }

        student_info = db_utils.get_student_info(student_id=uid)
        user_result['grade'] = student_info[0]
        school_code = student_info[1]

        user_result['school_info'] = {
            'school_code': school_code,
            'school_name': None,
            'school_address': None
        }
        if school_code:
            school_result = db_utils.get_school_info(school_code=school_code)
            if school_result:
                user_result['school_info'] = {
                    'school_code': school_result[0],
                    'school_name': school_result[1],
                    'school_address': school_result[2]
                }

        return dict({'user': user_result}, **SUCCESS_RESPONSE)


@UserNs.route('/parent/<uid>')
@require_auth
class UserParent(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.response(200, SUCCESS_VALUE, parent_user_info_model)
    def get(self, uid):
        """학부모 정보 조회"""
        user = db_utils.User.from_uid(uid)
        user_result = user.to_dict()

        students_info = db_utils.get_paired_students_info_of_parent(parent_id=uid)
        user_result['pairing_info'] = {
            'is_paired': len(students_info) != 0,
            'paired': students_info
        }
        return dict({'user': user_result}, **SUCCESS_RESPONSE)


@UserNs.route('/nickname/<nickname>')
class SearchNickname(Resource):
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def get(self, nickname: str):
        """Nickname 중복 검색"""
        result = db_utils.get_user_info_by_nickname(nickname)
        if not result:
            return SUCCESS_RESPONSE
        else:
            return FailResponse.DUPLICATED_NICKNAME


@UserNs.route('/email')
class SearchNickname(Resource):
    @UserNs.expect(email_check_model)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self: str):
        """email 중복 검색"""
        user_data: dict = request.form.to_dict()
        email = user_data.get('email')

        email_result = db_utils.get_user_info_by_email(email)
        if not email_result:
            return SUCCESS_RESPONSE
        else:
            user = db_utils.User.from_db_result(email_result)
            if user.active == 0:
                return FailResponse.INACTIVE_USER
            else:
                return FailResponse.REGISTERED_USER


@UserNs.route('/password')
@require_auth
class UpdatePassword(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.expect(update_password_model)
    def put(self):
        """password 업데이트"""
        user_data: dict = request.form.to_dict()
        uid = user_data.get('uid')
        passwd = user_data.get(PASSWORD)
        db_utils.update_password_of_user(uid=uid, passwd=passwd, verify_number='')  # TODO : check
        return SUCCESS_RESPONSE


@UserNs.route('/profile')
@require_auth
class UpdateUserProfile(LoginAuthResource):
    @UserNs.doc(params=AUTHORIZATION_HEADER)
    @UserNs.expect(user_profile_upload_model)
    @UserNs.response(200, SUCCESS_VALUE, user_profile_upload_output)
    def post(self):
        """유저 프로필 사진 업데이트"""
        image_dict = request.form.to_dict()
        uid = image_dict['uid']
        img_url = image_dict['img_url']

        user = db_utils.User.from_uid(uid)
        current_profile_number = user.profile_numbering
        profile_numbering = current_profile_number + 1

        utils.upload_user_profile_image(img_url, uid, profile_numbering)
        db_utils.update_user_profile_numbering(uid=uid, profile_numbering=profile_numbering)

        return dict({'profile_numbering': profile_numbering}, **SUCCESS_RESPONSE)


@UserNs.route('/academy')
class AcademyUser(Resource):
    @UserNs.expect(update_academy_model)
    def post(self):
        """academy 정보 수정"""
        academy_data: dict = request.json
        academy_id = academy_data.pop('academy_id')

        if 'img_url' in academy_data:
            img_url = academy_data.pop('img_url')
            utils.upload_academy_profile_image(img_url, academy_id)

        result = es_utils.update_document_content(index=ACADEMY_INDEX, doc_id=academy_id, content=academy_data)
        return result


@UserNs.route('/teacher')
class TeacherUser(Resource):
    @UserNs.expect(update_teacher_model)
    def post(self):
        """teacher 정보 수정"""
        teacher_data: dict = request.json
        teacher_id = teacher_data.pop('teacher_id')

        result = es_utils.update_document_content(index=TEACHER_INDEX, doc_id=teacher_id, content=teacher_data)
        return result


@UserNs.route('/allclass/notice')
class AllclassNotice(Resource):
    @UserNs.expect(get_allclass_notice_parameter)
    @UserNs.response(200, SUCCESS_VALUE, get_allclass_notice_output)
    def get(self):
        """올클래스 공지 게시판 글 조회"""
        allclass_notice_data = request.args
        doc_id = int(allclass_notice_data['doc_id'])

        db_result = db_utils.get_allclass_notice(doc_id=doc_id)
        if db_result:
            image_start_num = db_result[2]
            image_count = db_result[3]
            created_time = db_result[4]
            image_timestamp = created_time.strftime('%Y%m%d%H%M%S')

            images = []
            for i in range(image_start_num, image_start_num + image_count):
                images.append(f'allclass-{image_timestamp}-{i}')

            result = {'doc_id': doc_id, 'title': db_result[0], 'content': db_result[1], 'images': images,
                      'image_path': ALLCLASS_NOTICE_TABLE, 'created_time': created_time.strftime(DATE_FORMAT)}
            return dict({'data': result}, **SUCCESS_RESPONSE)
        return FAIL_RESPONSE

    @UserNs.expect(insert_academy_notice_model)
    def put(self):
        """올클래스 공지 게시판에 글 추가"""
        academy_notice_data = request.json
        images = academy_notice_data['img_url']
        image_count = len(images)

        now_date = datetime.now(timezone('Asia/Seoul'))
        created_time = now_date.strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')
        image_timestamp = now_date.strftime('%Y%m%d%H%M%S')

        for i, image in enumerate(images):
            file_name = f'allclass-{image_timestamp}-{i}'
            utils.upload_academy_notice_base64_image(ALLCLASS_NOTICE_TABLE, image, file_name)

        db_utils.insert_allclass_notice(title=academy_notice_data['title'], content=academy_notice_data['content'],
                                        image_count=image_count, created_time=created_time)
        return SUCCESS_RESPONSE

    @UserNs.expect(update_academy_notice_model)
    def post(self):
        """올클래스 공지 게시판에 글 수정"""
        academy_notice_data = request.json
        doc_id = academy_notice_data['doc_id']
        images = academy_notice_data['img_url']

        db_result = db_utils.get_allclass_notice(doc_id=doc_id)
        if db_result:
            modified_time = datetime.now(timezone('Asia/Seoul')).strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')
            image_start_num = db_result[2]
            image_count = db_result[3]

            if len(images) > 0:
                new_image_start_num = image_start_num + image_count
                new_image_count = len(images)

                created_time = db_result[4]
                image_timestamp = created_time.strftime('%Y%m%d%H%M%S')

                for i, image in enumerate(images):
                    file_name = f'allclass-{image_timestamp}-{new_image_start_num + i}'
                    utils.upload_academy_notice_base64_image(ALLCLASS_NOTICE_TABLE, image, file_name)
            else:
                new_image_start_num = image_start_num
                new_image_count = image_count

            db_utils.update_allclass_notice(doc_id=doc_id, title=academy_notice_data['title'],
                                            content=academy_notice_data['content'], modified_time=modified_time,
                                            image_start_num=new_image_start_num, image_count=new_image_count)
            return SUCCESS_RESPONSE
        return FAIL_RESPONSE


@UserNs.route('/allclass/notice/titles')
class AcademyNoticeTitles(Resource):
    @UserNs.expect(get_academy_notice_titles_parameter)
    @UserNs.response(200, SUCCESS_VALUE, get_academy_notice_titles_output)
    def get(self):
        """올클래스 공지 게시판의 title 조회"""
        academy_notice_data = request.args
        count = int(academy_notice_data['count']) if 'count' in academy_notice_data else None
        offset = int(academy_notice_data['offset']) if 'offset' in academy_notice_data else None
        result = []

        res = db_utils.get_titles_of_allclass_notice(count=count, doc_id=offset)
        if len(res) > 0:
            result = [{'doc_id': i[0], 'title': i[1], 'created_time': i[2].strftime(DATE_FORMAT)} for i in res]
            if result[0]['doc_id'] < result[-1]['doc_id']:
                result.reverse()
        return dict({'data': result}, **SUCCESS_RESPONSE)


# ----- SearchNs -----
@SearchNs.route('/teacher')
@UserNs.response(400, FAIL_VALUE, fail_response_model)
class SearchTeacher(Resource):
    @SearchNs.expect(search_teacher_parameter)
    @SearchNs.response(200, SUCCESS_VALUE, teacher_search_output)
    def get(self):
        """teacher_id 로 선생 검색"""
        args = request.args
        if 'teacher_id' in args:
            teacher_id = args['teacher_id']
            search_result = es_utils.get_document_by_document_id(index=TEACHER_INDEX, doc_id=teacher_id)
            return utils.build_response_from_es_result(search_result)

    @SearchNs.expect(teacher_search_conditions_input)
    @SearchNs.response(200, SUCCESS_VALUE, teacher_search_outputs)
    def post(self):
        """선생님 조건 검색"""
        request_form = request.form
        search_conditions: dict = request_form.to_dict()
        if 'tag_id' in search_conditions:
            search_conditions['tag_id'] = request_form.getlist('tag_id')

        if 'school_course' in search_conditions:
            search_conditions['school_course'] = request_form.getlist('school_course')

        if 'major_subject_id' in search_conditions:
            search_conditions['major_subject_id'] = request_form.getlist('major_subject_id')

        search_result = es_utils.search_teacher_info_from_conditions(search_conditions)
        return utils.build_response_from_es_result(search_result)


@SearchNs.route('/academy')
@UserNs.response(400, FAIL_VALUE, fail_response_model)
class SearchAcademy(Resource):
    @SearchNs.expect(search_academy_parameter)
    @SearchNs.response(200, SUCCESS_VALUE, academy_search_output)
    def get(self):
        """academy_id 로 학원 검색"""
        args = request.args
        if 'academy_id' in args:
            academy_id = args['academy_id']
            search_result = es_utils.get_document_by_document_id(index=ACADEMY_INDEX, doc_id=academy_id)
            return utils.build_response_from_es_result(search_result)

    @SearchNs.expect(academy_search_conditions_input)
    @SearchNs.response(200, SUCCESS_VALUE, academy_search_outputs)
    def post(self):
        """학원 조건 검색"""
        request_form = request.form
        search_conditions: dict = request_form.to_dict()
        if 'tag_id' in search_conditions:
            search_conditions['tag_id'] = request_form.getlist('tag_id')

        if 'school_course' in search_conditions:
            search_conditions['school_course'] = request_form.getlist('school_course')

        if 'major_subject_id' in search_conditions:
            search_conditions['major_subject_id'] = request_form.getlist('major_subject_id')

        if 'sort' in search_conditions:
            sort = request_form.getlist('sort')
            search_conditions['sort'] = utils.sorting_sort_values(sort, ['_score', 'class_count', '_id'])

        search_result = es_utils.search_academy_info_from_conditions(search_conditions)
        return utils.build_response_from_es_result(search_result)


@SearchNs.route('/class')
@UserNs.response(400, FAIL_VALUE, fail_response_model)
class SearchClass(Resource):
    @SearchNs.expect(search_class_conditions_input)
    @SearchNs.response(200, SUCCESS_VALUE, search_class_outputs)
    def post(self):
        """수업 조건 검색"""
        request_form = request.form
        search_conditions: dict = request_form.to_dict()
        if 'subject_id' in search_conditions:
            search_conditions['subject_id'] = request_form.getlist('subject_id')

        if 'week_day' in search_conditions:
            search_conditions['week_day'] = request_form.getlist('week_day')

        if 'sort' in search_conditions:
            sort = request_form.getlist('sort')
            search_conditions['sort'] = utils.sorting_sort_values(sort, ['_score', '_id'])

        search_result = es_utils.search_class_info_from_conditions(conditions=search_conditions)
        return utils.build_response_from_es_result(search_result)


@SearchNs.route('/school')
class SearchSchool(Resource):
    @SearchNs.expect(school_search_input)
    @SearchNs.response(200, SUCCESS_VALUE, school_search_output)
    @UserNs.response(400, FAIL_VALUE, fail_response_model)
    def post(self):
        """학교 검색"""
        search_conditions: dict = request.form.to_dict()
        if len(search_conditions) != 1:
            return dict({'reason': 'Search API receives only 1 search condition parameter'}, **FAIL_RESPONSE)
        search_result = utils.search_school_open_api(search_conditions)

        if search_result['result'] == FAIL_VALUE:
            return search_result

        result = []
        for row in search_result['data']:
            location = row['LCTN_SC_NM']

            result.append({'school_code': row['SD_SCHUL_CODE'],
                           'school_name': f"{row['SCHUL_NM']} ({location[:2]})",
                           'school_address': row['ORG_RDNMA']})

        return dict({'data': result}, **SUCCESS_RESPONSE)


@SearchNs.route('/tag')
class SearchTag(Resource):
    @SearchNs.response(200, SUCCESS_VALUE, search_tag_model)
    def get(self):
        if 'tag_id' in request.args:
            tags = db_utils.get_tag(tag_id=request.args['tag_id'])
        else:
            tags = db_utils.get_all_tags()

        return dict({'data': tags}, **SUCCESS_RESPONSE)


@SearchNs.route('/tag/address')
class SearchAddressTag(Resource):
    @SearchNs.response(200, SUCCESS_VALUE, search_address_tag_model)
    def get(self):
        if 'tag_id' in request.args:
            tags = db_utils.get_address_tag(tag_id=request.args['tag_id'])
        else:
            tags = db_utils.get_all_address_tags()

        return dict({'data': tags}, **SUCCESS_RESPONSE)


@SearchNs.route('/subject')
class SearchSubject(Resource):
    @SearchNs.expect(search_subject_parameter)
    @SearchNs.response(200, SUCCESS_VALUE, search_belonged_subjects_model)
    def get(self):
        """subject 정보 조회"""
        subject_args = request.args
        if 'belonged_subject' in subject_args:
            result = []
            belonged_subject = subject_args.get('belonged_subject')

            school_course = subject_args.get('school_course', None)
            if school_course:
                school_course = school_course.split(',')
            subject_result = db_utils.get_subject_by_belonged_subject_and_school_course(
                belonged_subject=belonged_subject, school_course=school_course
            )

            grade = subject_args.get('grade', None)
            if grade:
                grades = list(map(int, grade.split(',')))
                for subject in subject_result:
                    grade_info = subject[3]
                    if grade_info and (grade_info not in grades):
                        continue
                    result.append({'subject_id': subject[0],
                                   'subject_name': subject[1],
                                   'belonged_subject': subject[2],
                                   'grade': grade_info})
            else:
                for subject in subject_result:
                    result.append({'subject_id': subject[0],
                                   'subject_name': subject[1],
                                   'belonged_subject': subject[2],
                                   'grade': subject[3]})
            return dict({'data': result}, **SUCCESS_RESPONSE)

        if 'subject_id' in subject_args:
            subject_id = subject_args.get('subject_id')
            result = []

            subject_result = db_utils.get_subject(subject_id)
            for subject in subject_result:
                result.append({'subject_id': subject[0], 'subject_name': subject[1], 'belonged_subject': subject[2]})
            return dict({'data': result}, **SUCCESS_RESPONSE)


# ----- ClassNs -----
@ClassNs.route('')
@ClassNs.response(400, FAIL_VALUE, fail_response_model)
class Class(Resource):
    @ClassNs.expect(get_class_parameter)
    @ClassNs.response(200, SUCCESS_VALUE, get_class_output)
    def get(self):
        """class_id 로 class 정보 조회"""
        class_id = request.args.get(CLASS_ID)
        search_result = es_utils.get_document_by_document_id(index=CLASS_INDEX, doc_id=class_id)
        return utils.build_response_from_es_result(search_result)

    @ClassNs.expect(class_register_input)
    def post(self):
        """Class 등록"""
        class_data: dict = request.json

        essential_keys = [NAME, SUBJECT_INFO, REGULAR_SCHEDULE, 'start_date', 'end_date']
        check_response = utils.check_key_value_in_data_is_validate(class_data, essential_keys)
        if check_response['result'] == FAIL_VALUE:
            return check_response

        check_response = utils.check_key_value_in_data_is_validate(class_data[SUBJECT_INFO],
                                                                   SUBJECT_INFO_ESSENTIAL_KEYS)
        if check_response['result'] == FAIL_VALUE:
            return check_response

        result = es_utils.insert_class_info(class_data)
        if result['result'] == SUCCESS_VALUE:
            if ACADEMY_INFO in class_data:
                if 'academy_id' in class_data[ACADEMY_INFO]:
                    es_utils.upsert_class_count_of_academy(class_data[ACADEMY_INFO]['academy_id'])

        return result

    @ClassNs.expect(class_update_input)
    def put(self):
        """Class 업데이트"""
        class_data: dict = request.json

        essential_keys = [NAME, SUBJECT_INFO, REGULAR_SCHEDULE, CLASS_ID]
        check_response = utils.check_key_value_in_data_is_validate(class_data, essential_keys)
        if check_response['result'] == FAIL_VALUE:
            return check_response

        check_response = utils.check_key_value_in_data_is_validate(class_data[SUBJECT_INFO],
                                                                   SUBJECT_INFO_ESSENTIAL_KEYS)
        if check_response['result'] == FAIL_VALUE:
            return check_response

        class_id = class_data.pop(CLASS_ID)
        result = es_utils.insert_class_info(class_data, class_id=class_id)
        return result


# ----- ScheduleNs -----
@ScheduleNs.route('')
@require_auth
@ScheduleNs.doc(params=AUTHORIZATION_HEADER)
class GetSchedule(Resource):
    @ScheduleNs.expect(get_schedule_parameter_model)
    @ScheduleNs.response(200, SUCCESS_VALUE, search_schedule_output)
    def get(self):
        """스케줄 조회"""
        schedule_args: dict = request.args
        time_level = schedule_args['time_level']
        year = schedule_args['year']
        month = schedule_args['month']
        uid = schedule_args['uid']

        scheduler = Scheduler(uid=uid)
        if time_level == 'day':
            date = datetime.strptime(f'{year}-{month}-{schedule_args["day"]}', DATE_FORMAT)
            result = scheduler.get_day_schedule(date)

        elif time_level == 'week':
            monday_date = datetime.strptime(f'{year}-{month}-{schedule_args["day"]}', DATE_FORMAT)
            result = scheduler.get_week_schedule(monday_date)

        elif time_level == 'month':
            result = scheduler.get_month_schedule(year=year, month=month)

        else:
            raise Exception('time_level variable is not proper')

        return dict({'data': result}, **SUCCESS_RESPONSE)


@ScheduleNs.route('/class/preview/week')
class ScheduleWeekPreviewClass(Resource):
    @ClassNs.expect(get_class_parameter)
    @ScheduleNs.response(200, SUCCESS_VALUE, week_preview_schedule_class_model)
    def get(self):
        """class 의 첫 수업주 or 이번주 시간표 조회"""
        class_data: dict = request.args
        class_id = class_data[CLASS_ID]

        preview_schedule_of_class, monday_date = schedule.get_week_preview_schedule_of_class(class_id)
        result = {'schedule': preview_schedule_of_class, 'monday_date': monday_date}
        return dict({'data': result}, **SUCCESS_RESPONSE)


@ScheduleNs.route('/class/preview/month')
class ScheduleMonthPreviewClass(Resource):
    @ClassNs.expect(get_class_parameter)
    @ScheduleNs.response(200, SUCCESS_VALUE, month_preview_schedule_class_model)
    def get(self):
        """class 의 첫 수업달 or 이번달 시간표 조회"""
        class_data: dict = request.args
        class_id = class_data[CLASS_ID]

        preview_schedule_of_class, month, year = schedule.get_month_preview_schedule_of_class(class_id)
        result = {'schedule': preview_schedule_of_class, 'month': month, 'year': year}
        return dict({'data': result}, **SUCCESS_RESPONSE)


@ScheduleNs.route('/class')
class ClassSchedule(Resource):
    @ScheduleNs.expect(check_class_schedule_parameter_model)
    @ScheduleNs.response(200, SUCCESS_VALUE, search_schedule_output)
    def get(self):
        """class 의 해당 일,주,월에 따른 시간표 조회"""
        class_data: dict = request.args
        class_id = class_data[CLASS_ID]
        time_level = class_data['time_level']
        year = class_data['year']
        month = class_data['month']

        class_scheduler = Scheduler(class_id=class_id)
        if time_level == 'day':
            date = datetime.strptime(f'{year}-{month}-{class_data["day"]}', DATE_FORMAT)
            result = class_scheduler.get_day_schedule(date)

        elif time_level == 'week':
            monday_date = datetime.strptime(f'{year}-{month}-{class_data["day"]}', DATE_FORMAT)
            result = class_scheduler.get_week_schedule(monday_date)

        elif time_level == 'month':
            result = class_scheduler.get_month_schedule(year=year, month=month)

        else:
            raise Exception('time_level variable is not proper')

        return dict({'data': result}, **SUCCESS_RESPONSE)


@ScheduleNs.route('/regular')
@require_auth
@ScheduleNs.doc(params=AUTHORIZATION_HEADER)
class RegularSchedule(Resource):
    @ScheduleNs.expect(regular_schedule_query_model)
    def put(self):
        """regular schedule(class) 추가"""
        schedule_data: dict = request.form.to_dict()
        uid = schedule_data['uid']

        user = db_utils.User.from_uid(uid)
        if user.user_type not in [UserCode.STUDENT.value, UserCode.PARENT.value]:
            return FailResponse.improper_user_type_exception(user_type=user.user_type,
                                                             valid_user_types=[UserCode.STUDENT.value,
                                                                               UserCode.PARENT.value])
        class_id = schedule_data[CLASS_ID]

        ignore_overlap = schedule_data.get('ignore_overlap', DEFAULT_OVERLAP_FLAG)
        if ignore_overlap != IGNORE_OVERLAP_FLAG:
            overlap_result = schedule.check_class_overlap(uid, class_id)
            if len(overlap_result) > 0:
                return dict({'count': len(overlap_result),
                             'first_schedule': overlap_result[0]}, **FAIL_RESPONSE)

        return schedule.add_class_into_schedule(uid, class_id)

    @ScheduleNs.expect(regular_schedule_query_model)
    def delete(self):
        """regular class 삭제"""
        schedule_data: dict = request.form.to_dict()
        uid = schedule_data['uid']

        user = db_utils.User.from_uid(uid)
        if user.user_type not in [UserCode.STUDENT.value, UserCode.PARENT.value]:
            return FailResponse.improper_user_type_exception(user_type=user.user_type,
                                                             valid_user_types=[UserCode.STUDENT.value,
                                                                               UserCode.PARENT.value])
        class_id = schedule_data[CLASS_ID]
        if schedule.is_academy_class(class_id):
            return schedule.remove_class_from_schedule(uid, class_id)
        else:
            return FAIL_RESPONSE


@ScheduleNs.route('/custom')
@require_auth
@ScheduleNs.doc(params=AUTHORIZATION_HEADER)
class CustomSchedule(Resource):
    @ScheduleNs.expect(add_schedule_input_model)
    def put(self):
        """단일 custom schedule 추가"""
        schedule_data: dict = request.form.to_dict()
        year = schedule_data['year']
        month = schedule_data['month']
        day = schedule_data['day']

        uid = schedule_data['uid']
        user = db_utils.User.from_uid(uid)
        if user.user_type not in [UserCode.STUDENT.value, UserCode.PARENT.value]:
            return FailResponse.improper_user_type_exception(user_type=user.user_type,
                                                             valid_user_types=[UserCode.STUDENT.value,
                                                                               UserCode.PARENT.value])

        ignore_overlap = schedule_data.get('ignore_overlap', DEFAULT_OVERLAP_FLAG)
        if ignore_overlap != IGNORE_OVERLAP_FLAG:
            date = datetime.strptime(f'{year}-{month}-{day}', DATE_FORMAT)
            overlap_check = schedule.check_day_schedule_overlap(uid=uid, date=date,
                                                                start=schedule_data['start'],
                                                                end=schedule_data['end'])
            if overlap_check['result'] == FAIL_VALUE:
                if 'overlap_schedule_info' in overlap_check:
                    return FailResponse.overlap_schedule(overlap_check['overlap_schedule_info'])

        result = schedule.add_custom_schedule(uid=uid, year_month=f'{year}.{month}',
                                              day=day, schedule_data=schedule_data)
        return utils.build_response_from_es_result(result)

    @ScheduleNs.expect(update_schedule_input_model)
    @ScheduleNs.response(200, SUCCESS_VALUE, update_schedule_output_model)
    def post(self):
        """custom schedule 업데이트"""
        schedule_data: dict = request.form.to_dict()
        schedule_id = schedule_data[SCHEDULE_ID]
        uid = schedule_data['uid']

        if schedule_id.startswith(CLASS_PREFIX):
            class_result = es_utils.get_class_info(schedule_id)
            if class_result['result'] == FAIL_VALUE:
                return utils.build_response_from_es_result(class_result)

        if schedule_id.startswith(USER_CLASS_PREFIX):
            class_result = es_utils.get_user_class_info(schedule_id)
            if class_result['result'] == FAIL_VALUE:
                return utils.build_response_from_es_result(class_result)

        user = db_utils.User.from_uid(uid)
        if user.user_type not in [UserCode.STUDENT.value, UserCode.PARENT.value]:
            return FailResponse.improper_user_type_exception(user_type=user.user_type,
                                                             valid_user_types=[UserCode.STUDENT.value,
                                                                               UserCode.PARENT.value])
        description = schedule_data['description']
        original_year = schedule_data['original_year']
        original_month = schedule_data['original_month']
        new_year = schedule_data['new_year']
        new_month = schedule_data['new_month']

        original_time_info = {
            'year': original_year,
            'month': original_month,
            'day': schedule_data['original_day'],
            'start': schedule_data['original_start'],
            'end': schedule_data['original_end']
        }

        new_time_info = {
            'year': new_year,
            'month': new_month,
            'day': schedule_data['new_day'],
            'start': schedule_data['new_start'],
            'end': schedule_data['new_end']
        }
        if original_time_info == new_time_info:
            # 시간 정보가 같은 경우, description 만 업데이트
            schedule.update_schedule_description(uid=uid,
                                                 schedule_id=schedule_id,
                                                 year_month=f'{original_year}.{original_month}',
                                                 time_info=original_time_info,
                                                 description=description)
            schedule_id_dict = {SCHEDULE_ID: schedule_id}
        else:
            ignore_overlap = schedule_data.get('ignore_overlap', DEFAULT_OVERLAP_FLAG)
            if ignore_overlap != IGNORE_OVERLAP_FLAG:
                new_date = datetime.strptime(f'{new_year}-{new_month}-{schedule_data["new_day"]}', DATE_FORMAT)
                if original_time_info['day'] == new_time_info['day']:
                    overlap_check = schedule.check_day_schedule_overlap(uid=uid, date=new_date,
                                                                        start=schedule_data['new_start'],
                                                                        end=schedule_data['new_end'],
                                                                        schedule_id=schedule_id,
                                                                        original_time_info=original_time_info)
                else:
                    overlap_check = schedule.check_day_schedule_overlap(uid=uid, date=new_date,
                                                                        start=schedule_data['new_start'],
                                                                        end=schedule_data['new_end'])
                if overlap_check['result'] == FAIL_VALUE:
                    if 'overlap_schedule_info' in overlap_check:
                        return FailResponse.overlap_schedule(overlap_check['overlap_schedule_info'])

            update_result = schedule.update_schedule(uid=uid,
                                                     schedule_id=schedule_id,
                                                     original_time_info=original_time_info,
                                                     new_time_info=new_time_info,
                                                     description=description)
            if update_result['result'] == FAIL_VALUE:
                return utils.build_response_from_es_result(update_result)
            schedule_id_dict = update_result['schedule_id_dict']

        if schedule_id_dict[SCHEDULE_ID]:
            new_date = datetime.strptime(f'{new_year}-{new_month}-{schedule_data["new_day"]}', DATE_FORMAT)
            new_week_day = new_date.weekday()
            updated_info = {
                'date': {'year': new_date.year, 'month': new_date.month, 'day': new_date.day},
                'start': schedule_data['new_start'],
                'end': schedule_data['new_end'],
                'week_day': str(new_week_day),
                'description': description,
                SCHEDULE_ID: schedule_id_dict[SCHEDULE_ID]
            }
            return dict({'data': updated_info}, **SUCCESS_RESPONSE)
        else:
            return FailResponse.IMPROPER_SCHEDULE

    @ScheduleNs.expect(delete_schedule_input_model)
    def delete(self):
        """custom schedule 삭제"""
        schedule_data: dict = request.form.to_dict()
        year = schedule_data['year']
        month = schedule_data['month']

        schedule_id = schedule_data[SCHEDULE_ID]
        if not schedule.is_custom_schedule(schedule_id):
            if schedule.is_academy_class(schedule_id):
                class_result = es_utils.get_document_by_document_id(index=CLASS_INDEX, doc_id=schedule_id)
                if class_result['result'] == FAIL_VALUE:
                    return FailResponse.from_exception('Elasticsearch', class_result['error'])

            if schedule.is_user_class(schedule_id):
                class_result = es_utils.get_document_by_document_id(index=USER_CLASS_INDEX, doc_id=schedule_id)
                if class_result['result'] == FAIL_VALUE:
                    return FailResponse.from_exception('Elasticsearch', class_result['error'])

        uid = None
        if 'student_id' in schedule_data:
            uid = schedule_data['student_id']
        if 'uid' in schedule_data:
            uid = schedule_data['uid']
        if not uid:
            return FailResponse.missed_key_exception('uid, student_id', schedule_data)

        user = db_utils.User.from_uid(uid)
        if user.user_type not in [UserCode.STUDENT.value, UserCode.PARENT.value]:
            return FailResponse.improper_user_type_exception(user_type=user.user_type,
                                                             valid_user_types=[UserCode.STUDENT.value,
                                                                               UserCode.PARENT.value])

        update_result = schedule.add_schedule_delete(uid=uid,
                                                     schedule_id=schedule_id,
                                                     year_month=f'{year}.{month}',
                                                     schedule_data=schedule_data)
        return update_result


@ScheduleNs.route('/user/class')
@require_auth
@ScheduleNs.doc(params=AUTHORIZATION_HEADER)
class CustomRepeatSchedule(Resource):
    @ScheduleNs.expect(add_user_class_input_model)
    def put(self):
        """user class 추가"""
        schedule_data: dict = request.form.to_dict()

        uid = schedule_data['uid']
        user = db_utils.User.from_uid(uid)
        if user.user_type not in [UserCode.STUDENT.value, UserCode.PARENT.value]:
            return FailResponse.improper_user_type_exception(user_type=user.user_type,
                                                             valid_user_types=[UserCode.STUDENT.value,
                                                                               UserCode.PARENT.value])
        user_class_info = {
            'uid': uid,  # 일반 class info 와 다르게 uid 가 들어감
            'name': schedule_data['name'],
            'description': schedule_data['description'],
            'academy_info': {
                'academy_name': schedule_data['academy_name'],
                'academy_id': 'academy'
            },
            'teacher_info': [{
                'teacher_name': schedule_data['teacher_name'],
                'teacher_id': 'teacher'
            }],
            'start_date': schedule_data['start_date'],
            'end_date': schedule_data['end_date']
        }

        regular_schedule = []
        schedule_count = int(schedule_data['schedule_count'])
        for i in range(schedule_count):
            regular_schedule.append({
                "week_day": schedule_data[f'{i}_week_day'],
                "start": schedule_data[f'{i}_start'],
                "end": schedule_data[f'{i}_end'],
                "over_night": False
            })
        user_class_info['regular_schedule'] = regular_schedule

        ignore_overlap = schedule_data.get('ignore_overlap', DEFAULT_OVERLAP_FLAG)
        if ignore_overlap != IGNORE_OVERLAP_FLAG:
            overlap_result = schedule.check_user_class_overlap(uid, user_class_info)
            if len(overlap_result) > 0:
                return dict({'count': len(overlap_result),
                             'first_schedule': overlap_result[0]}, **FAIL_RESPONSE)

        insert_result = es_utils.insert_user_class_info(user_class_info)
        if insert_result['result'] == SUCCESS_VALUE:
            user_class_id = insert_result[USER_CLASS_ID]
            add_result = schedule.add_user_class_into_schedule(uid, user_class_info, user_class_id)
            return dict(add_result, **{SCHEDULE_ID: user_class_id, CLASS_ID: user_class_id})
        else:
            return insert_result

    @ScheduleNs.expect(delete_user_class_input_model)
    def delete(self):
        """user class 전체 삭제"""
        schedule_data: dict = request.form.to_dict()

        uid = schedule_data['uid']
        user = db_utils.User.from_uid(uid)
        if user.user_type not in [UserCode.STUDENT.value, UserCode.PARENT.value]:
            return FailResponse.improper_user_type_exception(user_type=user.user_type,
                                                             valid_user_types=[UserCode.STUDENT.value,
                                                                               UserCode.PARENT.value])
        class_id = schedule_data[CLASS_ID]
        if schedule.is_user_class(class_id):
            return schedule.delete_user_class(uid, class_id)
        else:
            return FAIL_RESPONSE


# ----- AcademyNs -----
@AcademyNs.route('/notice')
class AcademyNotice(Resource):
    @AcademyNs.expect(get_academy_notice_parameter)
    @AcademyNs.response(200, SUCCESS_VALUE, get_academy_notice_output)
    def get(self):
        """학원 공지 게시판 글 조회"""
        academy_notice_data = request.args
        academy_id = academy_notice_data['academy_id']
        doc_id = int(academy_notice_data['doc_id'])

        db_result = db_utils.get_academy_notice(notice_table=ACADEMY_NOTICE_TABLE, doc_id=doc_id, academy_id=academy_id)
        if db_result:
            academy_id_prefix = academy_id.split('-')[0]
            image_start_num = db_result[2]
            image_count = db_result[3]
            created_time = db_result[4]
            image_timestamp = created_time.strftime('%Y%m%d%H%M%S')

            images = []
            for i in range(image_start_num, image_start_num + image_count):
                images.append(f'{academy_id_prefix}-{image_timestamp}-{i}')

            result = {'doc_id': doc_id, 'title': db_result[0], 'content': db_result[1], 'images': images,
                      'image_path': ACADEMY_NOTICE_TABLE, 'created_time': created_time.strftime(DATE_FORMAT)}
            return dict({'data': result}, **SUCCESS_RESPONSE)
        return FAIL_RESPONSE

    @AcademyNs.expect(insert_academy_notice_model)
    def put(self):
        """학원 공지 게시판에 글 추가"""
        academy_notice_data = request.json
        academy_id = academy_notice_data['academy_id']
        images = academy_notice_data['img_url']
        image_count = len(images)

        now_date = datetime.now(timezone('Asia/Seoul'))
        created_time = now_date.strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')
        image_timestamp = now_date.strftime('%Y%m%d%H%M%S')

        academy_id_prefix = academy_id.split('-')[0]
        for i, image in enumerate(images):
            file_name = f'{academy_id_prefix}-{image_timestamp}-{i}'
            utils.upload_academy_notice_base64_image(ACADEMY_NOTICE_TABLE, image, file_name)

        db_utils.insert_academy_notice(notice_table=ACADEMY_NOTICE_TABLE, academy_id=academy_id,
                                       title=academy_notice_data['title'], content=academy_notice_data['content'],
                                       image_count=image_count, created_time=created_time)
        return SUCCESS_RESPONSE

    @AcademyNs.expect(update_academy_notice_model)
    def post(self):
        """학원 공지 게시판에 글 수정"""
        academy_notice_data = request.json
        doc_id = academy_notice_data['doc_id']
        academy_id = academy_notice_data['academy_id']
        images = academy_notice_data['img_url']

        db_result = db_utils.get_academy_notice(notice_table=ACADEMY_NOTICE_TABLE, doc_id=doc_id, academy_id=academy_id)
        if db_result:
            modified_time = datetime.now(timezone('Asia/Seoul')).strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')
            image_start_num = db_result[2]
            image_count = db_result[3]

            if len(images) > 0:
                new_image_start_num = image_start_num + image_count
                new_image_count = len(images)

                created_time = db_result[4]
                image_timestamp = created_time.strftime('%Y%m%d%H%M%S')

                academy_id_prefix = academy_id.split('-')[0]
                for i, image in enumerate(images):
                    file_name = f'{academy_id_prefix}-{image_timestamp}-{new_image_start_num + i}'
                    utils.upload_academy_notice_base64_image(ACADEMY_NOTICE_TABLE, image, file_name)
            else:
                new_image_start_num = image_start_num
                new_image_count = image_count

            db_utils.update_academy_notice(notice_table=ACADEMY_NOTICE_TABLE,
                                           doc_id=doc_id, academy_id=academy_id, title=academy_notice_data['title'],
                                           content=academy_notice_data['content'], modified_time=modified_time,
                                           image_start_num=new_image_start_num, image_count=new_image_count)
            return SUCCESS_RESPONSE
        return FAIL_RESPONSE


@AcademyNs.route('/all/notices')
class AcademyNotices(Resource):
    @AcademyNs.expect(get_all_academy_notice_titles_parameter)
    @AcademyNs.response(200, SUCCESS_VALUE, get_all_academy_notice_titles_output)
    def get(self):
        """ 전체 학원 공지 조회 """
        academy_notice_data = request.args
        count = int(academy_notice_data['count']) if 'count' in academy_notice_data else 10
        offset = int(academy_notice_data['offset']) if 'offset' in academy_notice_data else None

        res = db_utils.get_recent_academy_notices(count=count, doc_id=offset)
        result = [{'doc_id': i[0], 'title': i[1], 'academy_name': i[2], 'academy_id': i[3], 'created_time': i[4][2:]} for i in res]
        return dict({'data': result}, **SUCCESS_RESPONSE)


@AcademyNs.route('/notice/titles')
class AcademyNoticeTitles(Resource):
    @AcademyNs.expect(get_academy_notice_titles_parameter)
    @AcademyNs.response(200, SUCCESS_VALUE, get_academy_notice_titles_output)
    def get(self):
        """학원 공지 게시판의 title 조회"""
        academy_notice_data = request.args
        academy_id = academy_notice_data['academy_id']
        count = int(academy_notice_data['count']) if 'count' in academy_notice_data else None
        offset = int(academy_notice_data['offset']) if 'offset' in academy_notice_data else None
        result = []

        res = db_utils.get_titles_of_academy_notice(notice_table=ACADEMY_NOTICE_TABLE, academy_id=academy_id,
                                                    count=count, doc_id=offset)
        if len(res) > 0:
            result = [{'doc_id': i[0], 'title': i[1], 'created_time': i[2].strftime(DATE_FORMAT)} for i in res]
            if result[0]['doc_id'] < result[-1]['doc_id']:
                result.reverse()
        return dict({'data': result}, **SUCCESS_RESPONSE)


@AcademyNs.route('/class_notice')
class AcademyClassNotice(Resource):
    @AcademyNs.expect(get_academy_notice_parameter)
    @AcademyNs.response(200, SUCCESS_VALUE, get_academy_notice_output)
    def get(self):
        """수업 공지 게시판 글 조회"""
        academy_notice_data = request.args
        academy_id = academy_notice_data['academy_id']
        doc_id = int(academy_notice_data['doc_id'])

        db_result = db_utils.get_academy_notice(notice_table=ACADEMY_CLASS_NOTICE_TABLE,
                                                doc_id=doc_id, academy_id=academy_id)
        if db_result:
            academy_id_prefix = academy_id.split('-')[0]
            image_start_num = db_result[2]
            image_count = db_result[3]
            created_time = db_result[4]
            image_timestamp = created_time.strftime('%Y%m%d%H%M%S')

            images = []
            for i in range(image_start_num, image_start_num + image_count):
                images.append(f'{academy_id_prefix}-{image_timestamp}-{i}')

            result = {'doc_id': doc_id, 'title': db_result[0], 'content': db_result[1], 'images': images,
                      'image_path': ACADEMY_CLASS_NOTICE_TABLE, 'created_time': created_time.strftime(DATE_FORMAT)}
            return dict({'data': result}, **SUCCESS_RESPONSE)
        return FAIL_RESPONSE

    @AcademyNs.expect(insert_academy_notice_model)
    def put(self):
        """수업 공지 게시판에 글 추가"""
        academy_notice_data = request.json
        academy_id = academy_notice_data['academy_id']
        images = academy_notice_data['img_url']
        image_count = len(images)

        now_date = datetime.now(timezone('Asia/Seoul'))
        created_time = now_date.strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')
        image_timestamp = now_date.strftime('%Y%m%d%H%M%S')

        academy_id_prefix = academy_id.split('-')[0]
        for i, image in enumerate(images):
            file_name = f'{academy_id_prefix}-{image_timestamp}-{i}'
            utils.upload_academy_notice_base64_image(ACADEMY_CLASS_NOTICE_TABLE, image, file_name)

        db_utils.insert_academy_notice(notice_table=ACADEMY_CLASS_NOTICE_TABLE, academy_id=academy_id,
                                       title=academy_notice_data['title'], content=academy_notice_data['content'],
                                       image_count=image_count, created_time=created_time)
        return SUCCESS_RESPONSE

    @AcademyNs.expect(update_academy_notice_model)
    def post(self):
        """수업 공지 게시판에 글 수정"""
        academy_notice_data = request.json
        doc_id = academy_notice_data['doc_id']
        academy_id = academy_notice_data['academy_id']
        images = academy_notice_data['img_url']

        db_result = db_utils.get_academy_notice(notice_table=ACADEMY_CLASS_NOTICE_TABLE,
                                                doc_id=doc_id, academy_id=academy_id)
        if db_result:
            modified_time = datetime.now(timezone('Asia/Seoul')).strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')
            image_start_num = db_result[2]
            image_count = db_result[3]

            if len(images) > 0:
                new_image_start_num = image_start_num + image_count
                new_image_count = len(images)

                created_time = db_result[4]
                image_timestamp = created_time.strftime('%Y%m%d%H%M%S')

                academy_id_prefix = academy_id.split('-')[0]
                for i, image in enumerate(images):
                    file_name = f'{academy_id_prefix}-{image_timestamp}-{new_image_start_num + i}'
                    utils.upload_academy_notice_base64_image(ACADEMY_CLASS_NOTICE_TABLE, image, file_name)
            else:
                new_image_start_num = image_start_num
                new_image_count = image_count

            db_utils.update_academy_notice(notice_table=ACADEMY_CLASS_NOTICE_TABLE,
                                           doc_id=doc_id, academy_id=academy_id, title=academy_notice_data['title'],
                                           content=academy_notice_data['content'], modified_time=modified_time,
                                           image_start_num=new_image_start_num, image_count=new_image_count)
            return SUCCESS_RESPONSE
        return FAIL_RESPONSE


@AcademyNs.route('/class_notice/titles')
class AcademyClassNoticeTitles(Resource):
    @AcademyNs.expect(get_academy_notice_titles_parameter)
    @AcademyNs.response(200, SUCCESS_VALUE, get_academy_notice_titles_output)
    def get(self):
        """수업 공지 게시판의 title 조회"""
        academy_notice_data = request.args
        academy_id = academy_notice_data['academy_id']
        count = int(academy_notice_data['count']) if 'count' in academy_notice_data else None
        offset = int(academy_notice_data['offset']) if 'offset' in academy_notice_data else None
        result = []

        res = db_utils.get_titles_of_academy_notice(notice_table=ACADEMY_CLASS_NOTICE_TABLE,
                                                    academy_id=academy_id, count=count, doc_id=offset)
        if len(res) > 0:
            result = [{'doc_id': i[0], 'title': i[1], 'created_time': i[2].strftime(DATE_FORMAT)} for i in res]
            if result[0]['doc_id'] < result[-1]['doc_id']:
                result.reverse()
        return dict({'data': result}, **SUCCESS_RESPONSE)


# ----- AdvertisementNs -----
@AdvertisementNs.route('/banner')
class BannerAdvertisement(Resource):
    def get(self):
        """베너 광고 조회"""
        arg = request.args
        ad_id = arg['ad_id']
        result = db_utils.get_banner_advertisement(int(ad_id))
        if result:
            return dict({'data': {'ad_id': ad_id, 'ad_location_id': result[0], 'image': result[1],
                                  'redirect_url': result[2], 'description': result[3]}}, **SUCCESS_RESPONSE)
        else:
            return FAIL_RESPONSE

    def put(self):
        """베너 광고 추가"""
        advertise_data = request.json
        ad_location_id = advertise_data['ad_location_id']
        redirect_url = advertise_data['redirect_url']
        description = advertise_data['description']

        img_url = advertise_data['img_url']
        image = str(uuid.uuid4())
        utils.upload_advertisement_base64_image(ADVERTISEMENT_TABLE, img_url, image)

        now_date = datetime.now(timezone('Asia/Seoul'))
        created_time = now_date.strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')

        db_utils.insert_banner_advertisement(ad_location_id, image, redirect_url, description, created_time)
        return SUCCESS_RESPONSE

    def post(self):
        """베너 광고 수정"""
        advertise_data = request.json
        ad_id = advertise_data['ad_id']
        redirect_url = advertise_data['redirect_url']
        description = advertise_data['description']

        img_url = advertise_data['img_url']
        if img_url:
            image_name = str(uuid.uuid4())
            utils.upload_advertisement_base64_image(ADVERTISEMENT_TABLE, img_url, image_name)
        else:
            image_name = advertise_data['image_name']

        now_date = datetime.now(timezone('Asia/Seoul'))
        modified_time = now_date.strftime(f'{DATE_FORMAT} {H_M_S_FORMATE}')

        db_utils.update_banner_advertisement(ad_id, image_name, redirect_url, description, modified_time)
        return SUCCESS_RESPONSE


@AdvertisementNs.route('/banner/random')
class BannerAdvertisement(Resource):
    @AdvertisementNs.expect(get_random_advertisement_input)
    @AdvertisementNs.response(200, SUCCESS_VALUE, get_random_advertisement_output)
    def post(self):
        """베너 광고 랜덤 조회"""
        data = request.form.to_dict()
        uid = data['uid']  # 나중에 user 기반 광고 사용
        ad_location_id = int(data['ad_location_id'])
        result = db_utils.get_random_banner_advertisement_image_and_ad_id(ad_location_id)
        if result:
            return dict({'data': {'ad_id': result[0], 'image': result[1], 'redirect_url': result[2],
                                  'image_path': ADVERTISEMENT_TABLE}}, **SUCCESS_RESPONSE)
        else:
            return FAIL_RESPONSE


@AdvertisementNs.route('/banner/all')
class BannerAdvertisement(Resource):
    def get(self):
        """모든 베너 광고 조회(admin 용)"""
        result = db_utils.get_all_banner_advertisement()
        data = [{'ad_id': i[0], 'description': i[1], 'ad_location_id': i[2]} for i in result]
        return dict({'data': data}, **SUCCESS_RESPONSE)
