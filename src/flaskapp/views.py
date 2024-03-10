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
    @UserNs.expect(user_update_model)
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

@UserNs.route('/List')
class UserList(Resource):
    @UserNs.response(200, 'SUCCESS', user_list_model)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """유저 목록"""
        result = db_utils.get_user_list()

        data = [{
                "user_id": x[0],
                "user_email": x[1],
                "user_type": x[3],
                "register_num": x[5],
                "company_address": x[6],
                "manager_name": x[7],
                "manager_phone": x[8],
                "manager_depart": x[9],
                "manager_grade": x[10],
                "other": x[11],
                "approval": x[12],
                "id": x[13],
                "admin_name": x[14],
                "admin_phone": x[15],
                
            }
        for x in result]
            
        return data

@UserNs.route('/CheckId')
class CheckId(Resource):
    @UserNs.expect(user_check_id_model)
    @UserNs.response(200, 'SUCCESS', success_response_model)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """아이디중복확인"""
        check_data: dict = request.json

        essential_keys = ['id']
        check_response = utils.check_key_value_in_data_is_validate(data=check_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        result = db_utils.user_check_id(check_data['id'])

        res = {}
        if (result != None):
            res['result'] = 'fail'
            res['reason'] = 'Already Existing'
            res['error_message'] = '아이디가 중복됩니다.'
            return res
        
        return SUCCESS_RESPONSE

@CompanyNs.route('/Register')
class CompanyRegister(Resource):
    @CompanyNs.expect(company_register_request_model)
    @CompanyNs.response(200, 'SUCCESS', success_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """업체 등록"""
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
class CompanyUpdate(Resource):
    @CompanyNs.expect(company_data_model)
    @CompanyNs.response(200, 'SUCCESS', success_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """업체 수정"""
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
    
@CompanyNs.route('/List')
class CompanyList(Resource):
    @CompanyNs.response(200, 'SUCCESS', company_list_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """업체 목록"""
        result = db_utils.get_company_list()

        print(result)
        data = [{'id': i[0], 'register_num': i[1], 'company_name': i[2]} for i in result]
        return data

@CompanyNs.route('/Check')
class CompanyCheck(Resource):
    @CompanyNs.expect(company_check_model)
    @CompanyNs.response(200, 'SUCCESS', company_check_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """업체확인"""
        check_data: dict = request.json

        essential_keys = ['register_num']
        check_response = utils.check_key_value_in_data_is_validate(data=check_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        result = db_utils.company_check(check_data['register_num'])

        res = {}
        if (result == None):
            res['result'] = 'fail'
            res['reason'] = 'None Existing'
            res['error_message'] = '업체가 존재하지 않습니다.'
            return res
        
        res['result'] = 'SUCCESS'
        res['data'] = result[0]
        return res
        
@CompanyNs.route('/Delete')
class CompanyUpdate(Resource):
    @CompanyNs.expect(company_delete_model)
    @CompanyNs.response(200, 'SUCCESS', success_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def delete(self):
        """업체 삭제"""
        delete_data: dict = request.json

        essential_keys = ['str_ids']
        check_response = utils.check_key_value_in_data_is_validate(data=delete_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.delete_company(delete_data['str_ids'])

        return SUCCESS_RESPONSE

@ProjectNs.route('/Register')
class CompanyRegister(Resource):
    @ProjectNs.expect(company_register_request_model)
    @ProjectNs.response(200, 'SUCCESS', success_response_model)
    @ProjectNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """업체 등록"""
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
