from flask_restx import Namespace, reqparse
from flask_cors import cross_origin
from flaskapp.constants import *

from flaskapp.swagger_type import *

# ----- Namespace -----
UserNs = Namespace('user', path='/user', description='유저의 register, login, pairing 등을 위한 API',decorators=[cross_origin()])
CompanyNs = Namespace('company', path='/company', description='업체 API',decorators=[cross_origin()])
ProjectNs = Namespace('project', path='/project', description='프로젝트 API',decorators=[cross_origin()])

namespaces = [UserNs, CompanyNs, ProjectNs]


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

user_update_form = {
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

user_update_model = UserNs.model('user_update_model', user_update_form)

user_check_id_form = {
                        'id': fields.String()
                    }

user_check_id_model = UserNs.model('user_check_id_model', user_check_id_form)

user_data_form = {
                        'user_id': fields.Integer(),
                        'user_email': fields.String(),
                        'user_type': fields.Integer(),
                        "register_num": fields.String(),
                        'company_address': fields.String(),
                        'manager_name': fields.String(),
                        'manager_phone': fields.String(),
                        'manager_depart': fields.String(),
                        'manager_grade': fields.String(),
                        'other': fields.String(),
                        'approval': fields.Integer(),
                        'id': fields.String(),
                        'admin_name': fields.String(),
                        'admin_phone': fields.String(),
                        }

user_data_model = UserNs.model('user_data_model', user_data_form)

user_list_form = {
    'data': fields.List(fields.Nested(user_data_model))
}

user_list_model = UserNs.model('user_list_model', user_list_form)

company_register_request_form = {
                        'register_num': fields.String(),
                        'company_name': fields.String(),
                        }

company_register_request_model = CompanyNs.model('company_register_request_model', company_register_request_form)

company_data_form = {
                        'id': fields.Integer(),
                        'register_num': fields.String(),
                        'company_name': fields.String(),
                        }

company_data_model = CompanyNs.model('company_data_model', company_data_form)

company_list_response_form = {
                        'data': fields.List(fields.Nested(company_data_model))
                        }

company_list_response_model = CompanyNs.model('company_list_response_model', company_list_response_form)

company_delete_form = {
                        'str_ids': fields.String()
                        }

company_delete_model = CompanyNs.model('company_delete_model', company_delete_form)

company_check_form = {
                        'register_num': fields.String()
                    }

company_check_model = UserNs.model('company_check_model', company_check_form)

company_check_response_form = {
                        'result': fields.String(),
                        'company_name': fields.String()
                    }

company_check_response_model = UserNs.model('company_check_response_model', company_check_response_form)

project_register_form = {
                        'result': fields.String(),
                        'company_name': fields.String()
                    }

company_check_response_model = ProjectNs.model('company_check_response_model', company_check_response_form)

project_register_request_form = {
                        'year': fields.Integer(), 
                        'name': fields.String(), 
                        'user_id': fields.Integer(), 
                        'checklist_id': fields.Integer(),
                        'privacy_type': fields.Integer(),
                        }

project_register_request_model = ProjectNs.model('project_register_request_model', project_register_request_form)

project_schedule_form = {
            'create_from': fields.String(),
            'create_to': fields.String(),
            'self_check_from': fields.String(),
            'self_check_to': fields.String(),
            'imp_check_from': fields.String(),
            'imp_check_to': fields.String(),
}

project_schedule_model = ProjectNs.model('project_schedule_model', project_schedule_form)

project_set_schedule_request_form = {
                        'id': fields.Integer(), 
                        **project_schedule_form
                        }

project_set_schedule_request_model = ProjectNs.model('project_set_schedule_request_model', project_set_schedule_request_form)

project_get_schedule_request_form = {
                        'id': fields.Integer(), 
                        }

project_get_schedule_request_model = ProjectNs.model('project_get_schedule_request_model', project_get_schedule_request_form)

project_get_schedule_response_form = {
                        'result': fields.String(),
                        'data': fields.Nested(project_schedule_model),
                    }

project_get_schedule_response_model = ProjectNs.model('project_get_schedule_response_model', project_get_schedule_response_form)

project_data_form = {
                        'id': fields.Integer(), 
                        'year': fields.Integer(), 
                        'name': fields.String(), 
                        'user_id': fields.Integer(), 
                        'checklist_id': fields.Integer(),
                        'privacy_type': fields.Integer(),
                    }

project_data_model = ProjectNs.model('project_data_model', project_data_form)

project_list_form = {
    'data': fields.List(fields.Nested(project_data_model))
}

project_list_model = ProjectNs.model('project_list_model', project_list_form)