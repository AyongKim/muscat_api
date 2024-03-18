import copy
import logging
import random
import string
import uuid
import requests
import os
from datetime import datetime
from pytz import timezone
from werkzeug.exceptions import BadRequest

from flask import request, g, send_file
from flask_restx import Resource
from pymysql.err import Error
from twilio.rest import TwilioException

from flaskapp import app
from flaskapp import utils
from flaskapp import db_utils
from flaskapp.flask_namespaces import *
from flaskapp.constants import *
from flaskapp.enums import *
import html




@UserNs.route('/Login')
class Login(Resource):
    @UserNs.expect(user_login_request_model)
    @UserNs.response(200, 'SUCCESS', user_login_response_model)
    def post(self):
        """로그인"""
        login_data: dict = request.json
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
                        update_data['access_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                update_data['access_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
        result = db_utils.check_duplication(signup_data['user_email'], signup_data['id'])

        res = {}

        if (result != None):
            res['result'] = 'fail'
            res['reason'] = 'Already Existing'
            res['error_message'] = '이메일 또는 아이디가 중복됩니다.'
            return res
        
        essential_keys = ['user_email', 'user_password', 'id', 'user_type']
        check_response = utils.check_key_value_in_data_is_validate(data=signup_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        res['id'] = db_utils.register_user(signup_data)
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

        essential_keys = ['user_id']
        check_response = utils.check_key_value_in_data_is_validate(data=update_data, keys=essential_keys)

        res = {}

        if 'user_email' in update_data:
            result = db_utils.check_email_duplication_with_id(update_data['user_email'], update_data['user_id'])

            if (result != None):
                res['result'] = 'fail'
                res['reason'] = 'Already Existing'
                res['error_message'] = '이메일이 중복됩니다.'
                return res

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        if 'user_password' in update_data:
            if update_data['user_password'] == '':
                update_data.pop('user_password')

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
                "access_time": x[18].strftime('%Y-%m-%d %H:%M:%S')
            }
        for x in result]
            
        return data

@ProjectNs.route('/Consignor')
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
                "access_time": x[18].strftime('%Y-%m-%d %H:%M:%S')
            }
        for x in result]
            
        return data


@UserNs.route('/ApprovalList')
class UserApprovalList(Resource):
    @UserNs.response(200, 'SUCCESS', user_list_model)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """승인신청유저 목록"""
        result = db_utils.get_approval_user_list()

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
                "access_time": x[18].strftime('%Y-%m-%d %H:%M:%S')
            }
        for x in result]
            
        return data


@UserNs.route('/Detail')
class UserDetail(Resource):
    @UserNs.expect(user_detail_request_model)
    @UserNs.response(200, 'SUCCESS', user_data_model)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """유저 상세정보"""
        check_data: dict = request.json

        essential_keys = ['id']
        check_response = utils.check_key_value_in_data_is_validate(data=check_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        result = db_utils.user_detail_by_id(check_data['id'])

        if result != None:
            x = result
            data = {
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
                    "access_time": x[18].strftime('%Y-%m-%d %H:%M:%S'),
                    "company_name": x[19]
                }
            return data
        else:
            return FailResponse.NOT_REGISTERED_USER

@UserNs.route('/Delete')
class UserDelete(Resource):
    @CompanyNs.expect(user_delete_model)
    @CompanyNs.response(200, 'SUCCESS', success_response_model)
    @CompanyNs.response(400, 'FAIL', fail_response_model)
    def delete(self):
        """유저 삭제"""
        delete_data: dict = request.json

        essential_keys = ['str_ids']
        check_response = utils.check_key_value_in_data_is_validate(data=delete_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.delete_user(delete_data['str_ids'])

        return SUCCESS_RESPONSE

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
        
        res['id'] = db_utils.register_company(signup_data)
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
class ProjectRegister(Resource):
    @ProjectNs.expect(project_register_request_model)
    @ProjectNs.response(200, 'SUCCESS', success_response_model)
    @ProjectNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """프로젝트 등록"""
        register_data: dict = request.json
        
        essential_keys = ['year', 'name', 'user_id', 'checklist_id', 'privacy_type']
        check_response = utils.check_key_value_in_data_is_validate(data=register_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        res = {}
        res['id'] = db_utils.register_project(register_data)
        res['result'] = SUCCESS_VALUE
        
        return res

@ProjectNs.route('/Schedule')
class ProjectSchedule(Resource):
    @ProjectNs.expect(project_set_schedule_request_model)
    @ProjectNs.response(200, 'SUCCESS', success_response_model)
    @ProjectNs.response(400, 'FAIL', fail_response_model)
    def put(self):
        """프로젝트 일정 설정"""
        register_data: dict = request.json
        
        essential_keys = ['id', 'create_from', 'create_to', 'self_check_from', 'self_check_to', 'imp_check_from', 'imp_check_to']
        check_response = utils.check_key_value_in_data_is_validate(data=register_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.update_project_schedule(register_data)
        
        return SUCCESS_RESPONSE
    
    @ProjectNs.expect(project_get_schedule_request_model)
    @ProjectNs.response(200, 'SUCCESS', success_response_model)
    @ProjectNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """프로젝트 일정 조회"""
        register_data: dict = request.json
        
        essential_keys = ['id']
        check_response = utils.check_key_value_in_data_is_validate(data=register_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        res = {}
        data = db_utils.get_project_schedule(register_data['id'])

        if data == None:
            res['result'] = 'fail'
            res['reason'] = 'Non Existing'
            res['error_message'] = '프로젝트가 존재하지 않습니다.'
            return res
        
        x = data
        res['data'] = {
            'create_from': x[0].strftime('%Y-%m-%d'),
            'create_to': x[1].strftime('%Y-%m-%d'),
            'self_check_from': x[2].strftime('%Y-%m-%d'),
            'self_check_to': x[3].strftime('%Y-%m-%d'),
            'imp_check_from': x[4].strftime('%Y-%m-%d'),
            'imp_check_to': x[5].strftime('%Y-%m-%d'),
        }
        res['result'] = 'SUCCESS'
        
        return res

@ProjectNs.route('/List')
class UserList(Resource):
    @UserNs.response(200, 'SUCCESS', project_list_model)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """프로젝트 목록"""
        search_data: dict = request.json
        print(search_data)
        result = db_utils.get_project_list(search_data)

        data = [{
                'id': x[0], 
                'year': x[1],
                'name': x[2],
                'user_id': x[3],
                'checklist_id': x[4],
                'privacy_type': x[5],
            }
        for x in result]
            
        return data
    
@ProjectNs.route('/Years')
class Year(Resource):
    @UserNs.response(200, 'SUCCESS', year_list_form)
    @UserNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """프로젝트 목록"""
        result = db_utils.get_year_list()

        data = [x[0] for x in result]
            
        return data

@NoticeNs.route('/Register')
class NoticeRegister(Resource):
    @NoticeNs.expect(notice_register_request_model)
    @NoticeNs.response(200, 'SUCCESS', success_response_model)
    @NoticeNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """공지 등록"""
        register_data: dict = request.form.to_dict()
        

        now = datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M%S')
        register_data['attachment'] = ''

        if 'file' in request.files:
            f = request.files['file'] 
            f.filename = html.unescape(f.filename)
            if f.filename != '':
                os.makedirs('upload/' + timestamp)
                f.save('upload/' + timestamp + '/' + f.filename)
                register_data['attachment'] = f.filename
        
        essential_keys = ['project_id', 'title', 'content', 'create_by']
        check_response = utils.check_key_value_in_data_is_validate(data=register_data, keys=essential_keys)
        register_data['title'] = html.unescape(register_data['title'])
        register_data['content'] = html.unescape(register_data['content'])
        register_data['create_by'] = html.unescape(register_data['create_by'])

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        register_data['create_time'] = now.strftime('%Y-%m-%d %H:%M:%S')
        register_data['views'] = 0
        
        res = {}
        res['id'] = db_utils.register_notice(register_data)
        res['result'] = SUCCESS_VALUE
        
        return res

@NoticeNs.route('/Update')
class NoticeUpdate(Resource):
    @NoticeNs.expect(notice_update_request_model)
    @NoticeNs.response(200, 'SUCCESS', success_response_model)
    @NoticeNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """공지 수정"""
        update_data: dict = request.form.to_dict()
        

        essential_keys = ['notice_id', 'project_id', 'title', 'content', 'change']
        check_response = utils.check_key_value_in_data_is_validate(data=update_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        data = db_utils.get_notice_attachment(update_data['notice_id'])
        if data == None:
            return {'result': 'FAIL',
                      'reason': 'Non existing Notice',
                      'error_message': '공지가 존재하지 않습니다.'
                      }

        timestamp = data[0].strftime('%Y%m%d%H%M%S')

        if update_data['change'] == '1':
            update_data['attachment'] = ''

            f = request.files['file'] 
            if f.filename != '':
                if not os.path.exists('upload/' + timestamp):
                    os.makedirs('upload/' + timestamp)
                f.save('upload/' + timestamp + '/' + f.filename)
                update_data['attachment'] = f.filename
        
        db_utils.update_notice(update_data)
        
        return SUCCESS_RESPONSE

@NoticeNs.route('/Attachment')
class NoticeAttachment(Resource):
    def get(self):
        """"""
        id = request.args.get('id', '')

        data = db_utils.get_notice_attachment(id)

        if data != None and data[1] != '':
            return send_file('../upload/'+data[0].strftime('%Y%m%d%H%M%S')+'/' + data[1], as_attachment=True)
        
        return 'Not exist'
    
@NoticeNs.route('/List')
class NoticeList(Resource):
    @NoticeNs.response(200, 'SUCCESS', notice_list_model)
    @NoticeNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """공지 목록"""
        search_data: dict = request.json
        result = db_utils.get_notice_list(search_data)

        data = [{
                'id': x[0], 
                'project_name': x[1] if x[1] != None else '전체',
                'title': x[2],
                'create_by': x[3],
                'create_time': x[4].strftime('%Y-%m-%d %H:%M:%S'),
                'views': x[5],
                'attachment': x[6],
                'project_id': x[7],
            }
        for x in result]
            
        return data

@NoticeNs.route('/Detail')
class NoticeDetail(Resource):
    @NoticeNs.expect(notice_detail_request_model)
    @NoticeNs.response(200, 'SUCCESS', notice_detail_model)
    @NoticeNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """공지  상세정보"""
        check_data: dict = request.json

        essential_keys = ['id']
        check_response = utils.check_key_value_in_data_is_validate(data=check_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        result = db_utils.notice_detail_by_id(check_data['id'])

        if result != None:
            x = result
            data = {
                'id': x[0], 
                'project_name': x[1] if x[1] != None else '전체',
                'title': x[2],
                'content': x[3],
                'create_by': x[4],
                'create_time': x[5].strftime('%Y-%m-%d %H:%M:%S'),
                'views': x[6],
                'attachment': x[7],
                'project_id': x[8]
            }
            return data
        else:
            return FailResponse.NOT_REGISTERED_NOTICE

@NoticeNs.route('/Delete')
class NoticeDelete(Resource):
    @NoticeNs.expect(notice_delete_model)
    @NoticeNs.response(200, 'SUCCESS', success_response_model)
    @NoticeNs.response(400, 'FAIL', fail_response_model)
    def delete(self):
        """공지 삭제"""
        delete_data: dict = request.json

        essential_keys = ['str_ids']
        check_response = utils.check_key_value_in_data_is_validate(data=delete_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.delete_notice(delete_data['str_ids'])

        return SUCCESS_RESPONSE


# 문의  

@InquiryNs.route('/Register')
class InquiryRegister(Resource):
    @InquiryNs.expect(inquiry_register_request_model)
    @InquiryNs.response(200, 'SUCCESS', success_response_model)
    @InquiryNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """문의 등록"""
        inquiry_data: dict = request.json
        
        essential_keys = ['title', 'content', 'password', 'author']
        check_response = utils.check_key_value_in_data_is_validate(data=inquiry_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        inquiry_data['submit_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        res = {}
        res['id'] = db_utils.register_inquiry(inquiry_data)
        res['result'] = SUCCESS_VALUE
        
        return res


@InquiryNs.route('/List')
class InquiryList(Resource):
    @InquiryNs.response(200, 'SUCCESS', inquiry_list_model)
    @InquiryNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """문의 목록 조회"""
        result = db_utils.get_inquiry_list()

        data = [{
                'id': x[0], 
                'title': x[1],
                'content': x[2],
                'password': x[3],
                'author': x[4],
                'created_date': x[5].strftime('%Y-%m-%d %H:%M:%S'), 
            }
        for x in result]

        return data

@InquiryNs.route('/Delete')
class InquiryDelete(Resource):
    @InquiryNs.expect(inquiry_delete_model)
    @InquiryNs.response(200, 'SUCCESS', success_response_model)
    @InquiryNs.response(400, 'FAIL', fail_response_model)
    def delete(self):
        """문의 삭제"""
        delete_data: dict = request.json

        essential_keys = ['str_ids']
        check_response = utils.check_key_value_in_data_is_validate(data=delete_data, keys=essential_keys)

        if check_response['result'] == FAIL_VALUE:
            return check_response
        
        db_utils.delete_inquiry(delete_data['str_ids'])

        return SUCCESS_RESPONSE

# @InquiryNs.route('/Detail')
# class InquiryDetail(Resource):
#     @InquiryNs.expect(inquiry_detail_request_model)
#     @InquiryNs.response(200, 'SUCCESS', inquiry_detail_model)
#     @InquiryNs.response(400, 'FAIL', fail_response_model)
#     def post(self):
#         """문의 상세정보 조회"""
#         check_data: dict = request.json

#         essential_keys = ['id']
#         check_response = utils.check_key_value_in_data_is_validate(data=check_data, keys=essential_keys)

#         if check_response['result'] == FAIL_VALUE:
#             return check_response
        
#         result = db_utils.get_inquiry_detail(check_data['id'])

#         if result != None:
#             x = result
#             data = {
#                 'id': x[0], 
#                 'title': x[1],
#                 'content': x[2],
#                 'password': x[3],
#                 'author': x[4],
#                 'submit_date': x[5].strftime('%Y-%m-%d %H:%M:%S'),
#                 'status': x[6],
#             }
#             return data
#         else:
#             return FailResponse.NOT_EXISTING_INQUIRY

# @InquiryNs.route('/UpdateStatus')
# class InquiryUpdateStatus(Resource):
#     @InquiryNs.expect(inquiry_update_status_request_model)
#     @InquiryNs.response(200, 'SUCCESS', success_response_model)
#     @InquiryNs.response(400, 'FAIL', fail_response_model)
#     def post(self):
#         """문의 상태 업데이트"""
#         update_data: dict = request.json

#         essential_keys = ['id', 'status']
#         check_response = utils.check_key_value_in_data_is_validate(data=update_data, keys=essential_keys)

#         if check_response['result'] == FAIL_VALUE:
#             return check_response
        
#         db_utils.update_inquiry_status(update_data)
        
#         return SUCCESS_RESPONSE


 


#개인정보취급분류관리
# Assuming inquiry_register_request_model and the others are adjusted or new models are defined for PersonalCategory
@PersonalCategoryNs.route('/Register')
class PersonalCategoryRegister(Resource):
    @PersonalCategoryNs.expect(personal_category_register_model)  # Update this model according to your new schema
    @PersonalCategoryNs.response(200, 'SUCCESS', success_response_model)
    @PersonalCategoryNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """개인정보 취급 분류 등록"""
        category_data: dict = request.json
        
        essential_keys = ['personal_category', 'description']
        check_response = utils.check_key_value_in_data_is_validate(data=category_data, keys=essential_keys)

        if check_response['result'] == 'FAIL':
            return check_response
        
        category_data['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        res = {}
        res['id'] = db_utils.register_personal_category(category_data)
        res['result'] = 'SUCCESS'
        
        return res


@PersonalCategoryNs.route('/List')
class PersonalCategoryList(Resource):
    @PersonalCategoryNs.response(200, 'SUCCESS', personal_category_list_model)  # Update or define this model
    @PersonalCategoryNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """개인정보 취급 분류 목록 조회"""
        result = db_utils.get_personal_categories()

        data = [{
                'id': x[0], 
                'personal_category': x[1],
                'description': x[2],
                'created_date': x[3].strftime('%Y-%m-%d %H:%M:%S'),
            }
        for x in result]
            
        return data


@PersonalCategoryNs.route('/Delete')
class PersonalCategoryDelete(Resource):
    @PersonalCategoryNs.expect(personal_category_delete_model)  # Define or update this model
    @PersonalCategoryNs.response(200, 'SUCCESS', success_response_model)
    @PersonalCategoryNs.response(400, 'FAIL', fail_response_model)
    def delete(self):
        """개인정보 취급 분류 삭제"""
        delete_data: dict = request.json

        essential_keys = ['id']
        check_response = utils.check_key_value_in_data_is_validate(data=delete_data, keys=essential_keys)

        if check_response['result'] == 'FAIL':
            return check_response
        
        db_utils.delete_personal_category(delete_data['id'])

        return {'result': 'SUCCESS'}


#개인정보항목관리
@PersonalInfoNs.route('/Register')
class PersonalInfoRegister(Resource):
    @PersonalInfoNs.expect(personal_info_register_model)
    @PersonalInfoNs.response(200, '성공', success_response_model)
    @PersonalInfoNs.response(400, '실패', fail_response_model)
    def post(self):
        """새로운 개인정보 항목 등록"""
        item_data = request.json
        
        # 유효성 검사 로직
        필수_키 = ['sequence', 'standard_grade', 'intermediate_grade', 'item', 'merged1', 'merged2']
        검사_결과 = utils.check_key_value_in_data_is_validate(data=item_data, keys=필수_키)

        if 검사_결과['result'] == 'FAIL':
            return 검사_결과
        
        # 현재 날짜 및 시간 사용
        item_data['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        결과 = db_utils.register_personal_info_item(item_data)
        return {'id': 결과, 'result': '성공'}

@PersonalInfoNs.route('/List')
class PersonalInfoListByCategory(Resource):
    @PersonalInfoNs.expect(personal_info_category_list_request_model)
    @PersonalInfoNs.response(200, '성공', personal_info_list_model)
    @PersonalInfoNs.response(400, '실패')
    def post(self):
        """카테고리 ID에 의한 개인정보 항목 목록 조회"""
        request_data = request.json
        category_id = request_data.get('category_id')
        
        # 카테고리 ID를 이용한 개인정보 항목 목록 조회
        결과 = db_utils.get_personal_info_items_list(category_id)
        
        if 결과 is None or len(결과) == 0:
            return {'message': '해당 카테고리에 개인정보 항목이 없습니다.'}, 404
        
        return {'data': 결과}

@PersonalInfoNs.route('/Delete')
class PersonalInfoDelete(Resource):
    @PersonalInfoNs.expect(personal_info_delete_model)
    @PersonalInfoNs.response(200, '성공')
    def delete(self):
        """ID를 이용한 개인정보 항목 삭제"""
        삭제_데이터 = request.json
        db_utils.delete_personal_info_item(삭제_데이터['id'])
        return {'result': '성공'}




#체크리스트관리
@ChecklistNs.route('/Register')
class ChecklistRegister(Resource):
    @ChecklistNs.expect(checklist_register_model)  # 이 모델을 새 스키마에 맞게 업데이트
    @ChecklistNs.response(200, 'SUCCESS', success_response_model)
    @ChecklistNs.response(400, 'FAIL', fail_response_model)
    def post(self):
        """체크리스트 항목 등록"""
        checklist_data: dict = request.json
        
        essential_keys = ['checklist_item', 'description']
        check_response = utils.check_key_value_in_data_is_validate(data=checklist_data, keys=essential_keys)

        if check_response['result'] == 'FAIL':
            return check_response
        
        checklist_data['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        res = db_utils.register_checklist_item(checklist_data)
        return {'id': res, 'result': 'SUCCESS'}


@ChecklistNs.route('/List')
class ChecklistList(Resource):
    @ChecklistNs.response(200, 'SUCCESS', checklist_list_model)
    def post(self):
        """체크리스트 항목 목록 조회"""
        result = db_utils.get_checklist_items()

        data = [{
                'id': x[0], 
                'checklist_item': x[1],
                'description': x[2],
                'created_date': x[3].strftime('%Y-%m-%d %H:%M:%S'),
            }
        for x in result]
            
        return data


@ChecklistNs.route('/Delete')
class ChecklistDelete(Resource):
    @ChecklistNs.expect(checklist_delete_model)
    @ChecklistNs.response(200, 'SUCCESS')
    @ChecklistNs.response(400, 'FAIL')
    def delete(self):
        """체크리스트 항목 삭제"""
        delete_data: dict = request.json

        essential_keys = ['id']
        check_response = utils.check_key_value_in_data_is_validate(data=delete_data, keys=essential_keys)

        if check_response['result'] == 'FAIL':
            return check_response
        
        db_utils.delete_checklist_item(delete_data['id'])

        return {'result': 'SUCCESS'}
