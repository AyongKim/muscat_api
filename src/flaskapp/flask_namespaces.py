from flask_restx import Namespace, reqparse
from flask_cors import cross_origin
from flaskapp.constants import *

from flaskapp.swagger_type import *

# ----- Namespace -----
UserNs = Namespace('user', path='/user', description='유저의 register, login, pairing 등을 위한 API',decorators=[cross_origin()])
CompanyNs = Namespace('company', path='/company', description='업체 API',decorators=[cross_origin()])
ProjectNs = Namespace('project', path='/project', description='프로젝트 API',decorators=[cross_origin()])
ProjectDetailNs = Namespace('project_detail', path='/project_detail', description='프로젝트 현황 API',decorators=[cross_origin()])
NoticeNs = Namespace('notice', path='/notice', description='공지 API',decorators=[cross_origin()])
InquiryNs = Namespace('inquiry', path='/inquiry', description='문의 API',decorators=[cross_origin()])
PersonalCategoryNs = Namespace('personal_category', path='/personal_category', description='개인정보취급분류 API',decorators=[cross_origin()])
PersonalInfoNs = Namespace('personal_info', path='/personal_info', description='개인정보항목관리', decorators=[cross_origin()] )
ChecklistNs = Namespace('checklist', path='/checklist', description='체크리스트 API',decorators=[cross_origin()])


namespaces = [UserNs, CompanyNs, ProjectNs, NoticeNs, ChecklistNs, InquiryNs, PersonalCategoryNs, PersonalInfoNs, ProjectDetailNs]


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

delete_form = {
            'str_ids': fields.String()
            }
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
                        'user_type': fields.Integer(),#0:admin, 1:수탁사, 2: 위탁사
                        'user_email': fields.String(),
                        'id': fields.String(),
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

user_detail_request_form = {
                        'id': fields.Integer()
                    }
user_detail_request_model = UserNs.model('user_detail_request_model', user_detail_request_form)

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
                        'access_time': fields.String(),
                        }

user_data_model = UserNs.model('user_data_model', user_data_form)

user_list_form = {
    'data': fields.List(fields.Nested(user_data_model))
}

user_list_model = UserNs.model('user_list_model', user_list_form)

user_consignor_data_form = {
                        'user_id': fields.Integer(),
                        'name': fields.String(),
                        }

user_consignor_data_model = UserNs.model('user_consignor_data_model', user_consignor_data_form)

user_consignor_list_form = {
    'data': fields.List(fields.Nested(user_consignor_data_model))
}

user_consignor_list_model = UserNs.model('user_consignor_list_model', user_consignor_list_form)

user_delete_model = UserNs.model('user_delete_model', delete_form)

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



company_delete_model = CompanyNs.model('company_delete_model', delete_form)

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
                        'checker': fields.String(),
                    }

project_data_model = ProjectNs.model('project_data_model', project_data_form)

project_list_form = {
    'data': fields.List(fields.Nested(project_data_model))
}

project_list_model = ProjectNs.model('project_list_model', project_list_form)

notice_register_request_form = {
                        'project_id': fields.Integer(),
                        'title': fields.String(),
                        'content': fields.String(),
                        'create_by': fields.String(),
                        'file': fields.Raw()
                        }

notice_register_request_model = NoticeNs.model('notice_register_request_model', notice_register_request_form)

notice_update_request_form = {
                        'notice_id': fields.Integer(),
                        'project_id': fields.Integer(),
                        'title': fields.String(),
                        'content': fields.String(),
                        'change': fields.String(),
                        'file': fields.Raw()
                        }

notice_update_request_model = NoticeNs.model('notice_update_request_model', notice_update_request_form)

notice_data_form = {
                        'id': fields.Integer(), 
                        'project_name': fields.String(),
                        'title': fields.String(),
                        'create_by': fields.String(),
                        'create_time': fields.String(),
                        'attachment': fields.String(),
                        'views': fields.Integer(),
                        'project_id': fields.Integer(),
                    }

notice_data_model = NoticeNs.model('notice_data_model', notice_data_form)

notice_list_form = {
    'data': fields.List(fields.Nested(notice_data_model))
}

notice_list_model = NoticeNs.model('notice_list_model', notice_list_form)

notice_delete_model = NoticeNs.model('notice_delete_model', delete_form)

notice_detail_form = {
                        'id': fields.Integer(), 
                        'project_name': fields.String(),
                        'title': fields.String(),
                        'content': fields.String(),
                        'create_by': fields.String(),
                        'create_time': fields.String(),
                        'attachment': fields.String(),
                        'views': fields.Integer(),
                        'project_id': fields.Integer(),
                    }

notice_detail_model = NoticeNs.model('notice_detail_model', notice_detail_form)

notice_detail_request_form = {
                        'id': fields.Integer()
                    }
notice_detail_request_model = NoticeNs.model('notice_detail_request_model', notice_detail_request_form)

# 문의관련

inquiry_register_request_form = {
    'title': fields.String(),
    'content': fields.String(),
    'password': fields.String(),
    'author': fields.String(),
    'created_date': fields.String()
}

inquiry_register_request_model = InquiryNs.model('inquiry_register_request_model', inquiry_register_request_form)

inquiry_data_form = {
    'id': fields.Integer(),
    'title': fields.String(),
    'content': fields.String(),
    'password': fields.String(),
    'author': fields.String(),
    'created_date': fields.String()
}

inquiry_data_model = InquiryNs.model('inquiry_data_model', inquiry_data_form)

inquiry_list_form = {
    'data': fields.List(fields.Nested(inquiry_data_model))
}

inquiry_list_model = InquiryNs.model('inquiry_list_model', inquiry_list_form)

inquiry_delete_model = InquiryNs.model('inquiry_delete_model', delete_form)

#######################################333
 # 개인정보 취급 분류 등록 모델
personal_category_register_request_form = {
    'personal_category': fields.String(required=True, description="개인정보 취급 분류"),
    'description': fields.String(required=True, description="분류 설명"),
}

personal_category_register_model = PersonalCategoryNs.model('personal_category_register_request_model', personal_category_register_request_form)

# 개인정보 취급 분류 데이터 모델
personal_category_data_form = {
    'id': fields.Integer(description="분류 ID"),
    'personal_category': fields.String(description="개인정보 취급 분류"),
    'description': fields.String(description="분류 설명"),
    'created_date': fields.String(description="생성 날짜")
}

personal_category_data_model = PersonalCategoryNs.model('personal_category_data_model', personal_category_data_form)

# 개인정보 취급 분류 목록 모델
personal_category_list_form = {
    'data': fields.List(fields.Nested(personal_category_data_model))
}

personal_category_list_model = PersonalCategoryNs.model('personal_category_list_model', personal_category_list_form)

# 개인정보 취급 분류 삭제 모델
personal_category_delete_form = {
    'id': fields.Integer(required=True, description="삭제할 분류 ID")
}

personal_category_delete_model = PersonalCategoryNs.model('personal_category_delete_model', personal_category_delete_form)


#####################################3333
# 개인정보 항목 등록 모델
personal_info_register_form = {
    'sequence': fields.Integer(required=True, description="순서"),
    'standard_grade': fields.String(required=True, description="기준 등급"),
    'intermediate_grade': fields.String(required=True, description="중간 등급"),
    'item': fields.String(required=True, description="항목 설명"),
    'merged1': fields.Integer(required=True, description="합병 필드 1"),
    'merged2': fields.Integer(required=True, description="합병 필드 2"),
}

personal_info_register_model = PersonalInfoNs.model('personal_info_register_model', personal_info_register_form)

# 개인정보 항목 데이터 모델
personal_info_data_form = {
    'id': fields.Integer(description="항목 ID"),
    'sequence': fields.Integer(description="순서"),
    'standard_grade': fields.String(description="기준 등급"),
    'intermediate_grade': fields.String(description="중간 등급"),
    'item': fields.String(description="항목 설명"),
    'merged1': fields.Integer(description="합병 필드 1"),
    'merged2': fields.Integer(description="합병 필드 2"),
}

personal_info_data_model = PersonalInfoNs.model('personal_info_data_model', personal_info_data_form)

# 개인정보 항목 목록 모델
personal_info_list_form = {
    'data': fields.List(fields.Nested(personal_info_data_model))
}

personal_info_list_model = PersonalInfoNs.model('personal_info_list_model', personal_info_list_form)


# 카테고리 ID를 입력으로 받는 모델 정의
personal_info_category_list_request_form = {
    'category_id': fields.Integer(required=True, description="조회할 개인정보 항목의 카테고리 ID")
}

personal_info_category_list_request_model = PersonalInfoNs.model('personal_info_category_list_request_model', personal_info_category_list_request_form)

# 개인정보 항목 삭제 모델
personal_info_delete_form = {
    'id': fields.Integer(required=True, description="삭제할 항목 ID")
}

personal_info_delete_model = PersonalInfoNs.model('personal_info_delete_model', personal_info_delete_form)



####################################33
# 체크리스트 등록 모델
checklist_register_request_form = {
    'checklist_item': fields.String(required=True, description="체크리스트 항목"),
    'description': fields.String(required=True, description="항목 설명"),
}

checklist_register_model = ChecklistNs.model('checklist_register_request_model', checklist_register_request_form)

# 체크리스트 데이터 모델
checklist_data_form = {
    'id': fields.Integer(description="항목 ID"),
    'checklist_item': fields.String(description="체크리스트 항목"),
    'description': fields.String(description="항목 설명"),
    'created_date': fields.String(description="생성 날짜")
}

checklist_data_model = ChecklistNs.model('checklist_data_model', checklist_data_form)

# 체크리스트 목록 모델
checklist_list_form = {
    'data': fields.List(fields.Nested(checklist_data_model))
}

checklist_list_model = ChecklistNs.model('checklist_list_model', checklist_list_form)

# 체크리스트 삭제 모델
checklist_delete_form = {
    'id': fields.Integer(required=True, description="삭제할 항목 ID")
}

checklist_delete_model = ChecklistNs.model('checklist_delete_model', checklist_delete_form)


year_form = {
    'year': fields.Integer()
}

year_model = ProjectNs.model('year_model', year_form)

year_list_form = {
                        'years': fields.List(fields.Nested(year_model))
                    }

year_list_model = ProjectNs.model('year_list_model', year_list_form)

project_detail_request_form = {
                        'id': fields.Integer()
                    }
project_detail_request_model = ProjectDetailNs.model('project_detail_request_model', project_detail_request_form)


project_detail_data_form = {
                        'id': fields.Integer(), 
                        'user_id': fields.Integer(), 
                        'user_name': fields.String(), 
                        'work_name': fields.String(), 
                        'checker_id': fields.Integer(), 
                        'checker_name': fields.String(), 
                        'check_type': fields.String(), 
                    }

project_detail_data_model = ProjectDetailNs.model('project_detail_data_model', project_detail_data_form)

project_detail_list_form = {
    'data': fields.List(fields.Nested(project_detail_data_model))
}

project_detail_list_model = ProjectDetailNs.model('project_detail_list_model', project_detail_list_form)

project_detail_register_request_form = {
                        'project_id': fields.Integer(), 
                        'user_id': fields.Integer(), 
                        'work_name': fields.String(), 
                        'checker_id': fields.Integer(), 
                        'check_type': fields.Integer(),
                        }

project_detail_register_request_model = ProjectDetailNs.model('project_detail_register_request_model', project_detail_register_request_form)


user_consignee_data_form = {
                        'user_id': fields.Integer(),
                        'name': fields.String(),
                        'company_address': fields.String(),
                        'manager_name': fields.String(),
                        'manager_phone':  fields.String()
                        }

user_consignee_data_model = UserNs.model('user_consignee_data_model', user_consignee_data_form)

user_consignee_list_form = {
    'data': fields.List(fields.Nested(user_consignee_data_model))
}

user_consignee_list_model = UserNs.model('user_consignee_list_model', user_consignee_list_form)

project_detail_delete_model = ProjectDetailNs.model('project_detail_delete_model', delete_form)

project_detail_update_form = {
                        'id': fields.Integer(),
                        'user_id': fields.Integer(), 
                        'work_name': fields.String(), 
                        'checker_id': fields.Integer(), 
                        'check_type': fields.Integer(),
                        'delay': fields.String(),
                        'create_date': fields.String(),
                        'self_check_date': fields.String(),
                        'imp_check_date': fields.String(),
                        }

project_detail_update_model = ProjectDetailNs.model('project_detail_update_model', project_detail_update_form)

project_detail_get_request_form = {
                        'project_id': fields.Integer(),
                        'admin_id': fields.Integer(), 
                        'consignee_id': fields.Integer(), 
                        }

project_detail_get_request_model = ProjectDetailNs.model('project_detail_get_request_model', project_detail_get_request_form)

project_detail_get_response_form = {
                        'id': fields.Integer(),
                        'create_date': fields.String(),
                        'self_check_date': fields.String(),
                        'imp_check_date': fields.String(),
                        'delay': fields.String(),
                    }

project_detail_get_response_model = ProjectDetailNs.model('project_detail_get_response_model', project_detail_get_response_form)

project_detail_check_schedule_request_form = {
                        'admin_id': fields.Integer(),
                        'project_id': fields.Integer()
                    }
project_detail_check_schedule_request_model = ProjectDetailNs.model('project_detail_check_schedule_request_model', project_detail_check_schedule_request_form)
