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
from flaskapp.flask_namespaces import *
from flaskapp.constants import *

@UserNs.route('/Login')
class Login(Resource):
    @UserNs.expect(user_login_request_model)
    @UserNs.response(200, 'SUCCESS', user_login_response_model)
    def post(self):
        """로그인"""
        login_data: dict = request.json
        print(login_data)
        result = db_utils.check_login(login_data['email'], login_data['password'])

        res={}
        if (result == None):
            res['loginResult'] = 2
        else:
            if 'code' in login_data:
                today = datetime.today()
                if result[3]:
                    diff = today - result[3]

                    if login_data['code'] == result[2] and diff.total_seconds() < 180:
                        res['loginResult'] = 1
                        res['userData'] = {}
                        res['userData']['userEmail'] = result[0]
                        res['userData']['userType'] = result[1]

                        update_data={}
                        update_data['user_id'] = result[4]
                        update_data['code'] = ''
                        db_utils.update_user(update_data)
                    else:
                        res['loginResult'] = 2
                else:
                    res['loginResult'] = 2
            else:
                res['loginResult'] = 1
                res['authRequired'] = True

                new_code = ''.join(str(random.randrange(1, 10)) for i in range(0, 8))

                update_data={}
                update_data['user_id'] = result[4]
                update_data['code'] = new_code
                update_data['updated_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db_utils.update_user(update_data)

                utils.send_mail(result[0], '인증메일 발송', f'로그인을 위한 인증정보입니다.\n아래의 인증번호를 입력하여 인증을 완료해주세요.\n인증메일: {new_code} (유효시간: 3분)')
            
        return res

@UserNs.route('/Signup')
class Signup(Resource):
    @UserNs.expect(user_signup_request_model)
    @UserNs.response(200, 'SUCCESS', success_response_model)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """등록"""
        signup_data: dict = request.json
        result = db_utils.check_duplication(signup_data['user_email'], signup_data['nickname'])

        res = {}

        if (result != None):
            res['result'] = 'fail'
            res['reason'] = 'Already Existing'
            res['error_message'] = '이메일 또는 아이디가 중복됩니다.'
            return res
        
        essential_keys = ['user_email', 'user_password', 'nickname', 'user_type']
        check_response = utils.check_key_value_in_data_is_validate(data=signup_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.register_user(signup_data)
        res['result'] = 'success'
        
        return res

@UserNs.route('/Update')
class Update(Resource):
    @UserNs.expect(user_update_request_model)
    @UserNs.response(200, 'SUCCESS', success_response_model)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """수정"""
        update_data: dict = request.json

        res = {}

        if 'user_email' in update_data:
            result = db_utils.check_duplication(update_data['user_email'])

            if (result != None):
                res['result'] = 'fail'
                res['reason'] = 'Already Existing'
                res['error_message'] = '이메일이 중복됩니다.'
                return res
        
        essential_keys = ['user_id']
        check_response = utils.check_key_value_in_data_is_validate(data=update_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.update_user(update_data)
        res['result'] = 'success'
        
        return res

@CompanyNs.route('/Register')
class CompanyRegister(Resource):
    @CompanyNs.expect(company_register_request_model)
    @CompanyNs.response(200, 'SUCCESS', success_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """등록"""
        signup_data: dict = request.json
        result = db_utils.check_company_duplication(signup_data['register_num'])

        res = {}

        if (result != None):
            res['result'] = 'fail'
            res['reason'] = 'Already Existing'
            res['error_message'] = '번호가 중복됩니다.'
            return res
        
        essential_keys = ['register_num', 'company_name']
        check_response = utils.check_key_value_in_data_is_validate(data=signup_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.register_company(signup_data)
        res['result'] = 'success'
        
        return res

@CompanyNs.route('/Update')
class CompanyRegister(Resource):
    @CompanyNs.expect(company_update_request_model)
    @CompanyNs.response(200, 'SUCCESS', success_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """수정"""
        update_data: dict = request.json
        result = db_utils.check_company_duplication(update_data['register_num'])

        res = {}

        if (result != None):
            res['result'] = 'fail'
            res['reason'] = 'Already Existing'
            res['error_message'] = '번호가 중복됩니다.'
            return res
        
        essential_keys = ['id']
        check_response = utils.check_key_value_in_data_is_validate(data=update_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.update_company(update_data)
        res['result'] = 'success'
        
        return res