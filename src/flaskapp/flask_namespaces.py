from flask_restx import Namespace, reqparse
from flask_cors import cross_origin

from flaskapp.swagger_type import *

# ----- Namespace -----
UserNs = Namespace('user', path='/user', description='유저의 register, login, pairing 등을 위한 API',decorators=[cross_origin()])

namespaces = [UserNs]


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

## User
get_academy_info_agree_form = {'get_academy_info': get_academy_info_flag}
update_academy_info_agree_form = {'uid': uid_field, 'get_academy_info': get_academy_info_flag}

user_token_info_form = {'uid': uid_field,
                        'user_type': user_type_field,
                        'nickname': nickname_field}
user_token_info_model = UserNs.model('user_token_info', user_token_info_form)
