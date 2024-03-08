from flask_restx import Namespace, reqparse
from flask_cors import cross_origin

from flaskapp.swagger_type import *

# ----- Namespace -----
UserNs = Namespace('user', path='/user', description='유저의 register, login, pairing 등을 위한 API',decorators=[cross_origin()])
CompanyNs = Namespace('company', path='/company', description='업체 API',decorators=[cross_origin()])

namespaces = [UserNs, CompanyNs]


def _data_response_model(data_form, ns, model_name, list_form=False, data_key='data', sort_result=False):
    ns_model = ns.model(f'{model_name}_model', data_form)
    if list_form:
        data_list_form = dict({data_key: fields.List(fields.Nested(ns_model))}, **success_response_form)
        if sort_result:
            data_list_form['sort'] = fields.List(sort_field)
        return ns.model(f'{model_name}_list_output_model', data_list_form)
    else:
        data_list_form = dict({data_key: fields.Nested(ns_model)}, **success_response_form)
        return ns.model(f'{model_name}_output_model', data_list_form)


# ----- Swagger Data Form -----
success_response_form = {'result': success_field}
fail_response_form = {'result': fail_field,
                      'reason': error_reason_field,
                      'error_message': error_message_field}
success_response_model = UserNs.model('success_response_model', success_response_form)
fail_response_model = UserNs.model('fail_response_model', fail_response_form)

## User
user_login_request_form = {'email': fields.String('a@a.a'),
                         'password': fields.String('password'),
                         'code': fields.String()
                         }

user_login_request_model = UserNs.model('user_login_request_model', user_login_request_form)

user_login_data_form = {'userEmail': fields.String('a@a.a'),
                         'userType': fields.Integer(1)}
user_login_data_model = UserNs.model('data', user_login_data_form)

user_login_response_form = {'loginResult': fields.Integer(1),
                            'userData': fields.Nested(user_login_data_model)
                            }

user_login_response_model = UserNs.model('user_login_response_model', user_login_response_form)

user_signup_request_form = {
                        'user_type': fields.Integer(),#1:admin, 2:수탁사, 3: 위탁사
                        'user_email': fields.String(description="asd"),
                        'nickname': fields.String(),
                        'user_password': fields.String(),
                        'register_num': fields.String(),
                        'company_address': fields.String(),
                        'manager_name': fields.String(),
                        'manager_phone': fields.String(),
                        'manager_depart': fields.String(),
                        'manager_grade': fields.String(),
                        'other': fields.String(),
                        'admin_name': fields.String(),
                        'admin_phone': fields.String(),
                        }

user_signup_request_model = UserNs.model('user_signup_request_model', user_signup_request_form)

user_update_request_form = {
                        'user_id': fields.Integer(),
                        'user_email': fields.String(),
                        'user_password': fields.String(),
                        'company_address': fields.String(),
                        'manager_name': fields.String(),
                        'manager_phone': fields.String(),
                        'manager_depart': fields.String(),
                        'manager_grade': fields.String(),
                        'other': fields.String(),
                        'admin_name': fields.String(),
                        'admin_phone': fields.String(),
                        'approval': fields.Integer(),
                        }

user_update_request_model = UserNs.model('user_update_request_model', user_update_request_form)

company_register_request_form = {
                        'register_num': fields.String(),
                        'company_name': fields.String(),
                        }

company_register_request_model = CompanyNs.model('company_register_request_model', company_register_request_form)

company_update_request_form = {
                        'id': fields.Integer(),
                        'register_num': fields.String(),
                        'company_name': fields.String(),
                        }

company_update_request_model = CompanyNs.model('company_update_request_model', company_update_request_form)