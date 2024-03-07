from flask_restx import Namespace, reqparse

from flaskapp.swagger_type import *

# ----- Namespace -----
UserNs = Namespace('user', path='/user', description='유저의 register, login, pairing 등을 위한 API')
SearchNs = Namespace('search', path='/search', description='학원, 선생, 강의 검색 API')
ClassNs = Namespace('class', path='/class', description='수업 관련 API')
ScheduleNs = Namespace('schedule', path='/schedule', description='개인 스케줄 생성, 업데이트, 조회 API')
AcademyNs = Namespace('academy', path='/academy', description='학원 API')
AdvertisementNs = Namespace('advertisement', path='/advertisement', description='광고 API')

namespaces = [UserNs, SearchNs, ClassNs, ScheduleNs, AcademyNs, AdvertisementNs]


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

date_form = {'year': year_field, 'month': month_field, 'day': day_field}
date_model = ScheduleNs.model('data', date_form)

school_info_form = {'school_code': school_code_field,
                    'school_name': school_name_field,
                    'school_address': address_field}
school_info_model = SearchNs.model('school_info', school_info_form)

address_tag_form = {'address_tag_id': tag_id_field,
                    'address_tag_name': address_tag_name_filed}
address_tag_model = SearchNs.model('address_tag', address_tag_form)
address_info_form = {'address': address_field,
                     'address_tag': fields.List(fields.Nested(address_tag_model))}
address_info_model = SearchNs.model('address_info', address_info_form)

## User
get_academy_info_agree_form = {'get_academy_info': get_academy_info_flag}
update_academy_info_agree_form = {'uid': uid_field, 'get_academy_info': get_academy_info_flag}

user_token_info_form = {'uid': uid_field,
                        'user_type': user_type_field,
                        'nickname': nickname_field}
user_token_info_model = UserNs.model('user_token_info', user_token_info_form)

subject_info_form = {'major_subject_name': subject_name_field,
                     'major_subject_id': subject_id_field,
                     'subject_name': subject_name_field,
                     'subject_id': subject_id_field,
                     'school_course': fields.List(school_course_field),
                     'grade': fields.List(grade_field)}
subject_info_model = UserNs.model('subject_info', subject_info_form)

academy_info_form = {'academy_name': academy_name_field,
                     'academy_id': uid_field,
                     'address_tag': fields.List(fields.Nested(address_tag_model))}
academy_info_model = UserNs.model('academy_info', academy_info_form)

teacher_info_form = {'teacher_name': teacher_name_field,
                     'teacher_id': uid_field}
teacher_info_model = UserNs.model('teacher_info', teacher_info_form)

sns_register_user_form = {'provider': provider_field,
                          'provider_id': provider_id_field,
                          'phone_number': phone_number_field}
sns_register_user_with_agree_form = dict({'get_academy_info': get_academy_info_flag,
                                          'provide_personal_info': provide_personal_info_flag},
                                         **sns_register_user_form)

sns_student_user_form = dict({'user_type': student_user_type_field,
                              'nickname': nickname_field,
                              'phone_number': phone_number_field},
                             **sns_register_user_with_agree_form)

sns_parent_user_form = dict({'name': user_name_field,
                             'user_type': parent_user_type_field,
                             'gender': gender_field,
                             'birthday': birthday_field,
                             'nickname': nickname_field},
                            **sns_register_user_with_agree_form)

self_register_user_form = {'email': email_field,
                           'password': password_field,
                           'provider': provider_field,
                           'phone_number': phone_number_field}
self_register_user_with_agree_form = dict({'get_academy_info': get_academy_info_flag,
                                           'provide_personal_info': provide_personal_info_flag},
                                          **self_register_user_form)

self_student_user_form = dict({'name': user_name_field,
                               'user_type': student_user_type_field,
                               'gender': gender_field,
                               'birthday': birthday_field,
                               'nickname': nickname_field,
                               'phone_number': phone_number_field,
                               'school_code': school_code_field},
                              **self_register_user_with_agree_form)

self_parent_user_form = dict({'name': user_name_field,
                              'user_type': parent_user_type_field,
                              'gender': gender_field,
                              'birthday': birthday_field,
                              'nickname': nickname_field,
                              'phone_number': phone_number_field},
                             **self_register_user_with_agree_form)

self_academy_user_form = dict({'name': user_name_field,
                               'user_type': academy_user_type_field,
                               'homepage_url': homepage_url_field,
                               'account_number': account_number_field,
                               'address_info': fields.Nested(address_info_model),
                               'subject_info': fields.List(fields.Nested(subject_info_model))},
                              **self_register_user_form)

self_teacher_user_form = dict({'name': user_name_field,
                               'user_type': teacher_user_type_field,
                               'gender': gender_field,
                               'birthday': birthday_field,
                               'account_number': account_number_field,
                               'subject_info': fields.List(fields.Nested(subject_info_model)),
                               'academy_info': fields.List(fields.Nested(academy_info_model))},
                              **self_register_user_form)

student_pairing_form = {'uid': uid_field,
                        'name': user_name_field}
parent_pairing_form = dict(student_pairing_form, **{'selected': selected_field})
student_pairing_model = UserNs.model('pairing', student_pairing_form)
parent_pairing_model = UserNs.model('pairing', parent_pairing_form)
pairing_info_form = {'is_paired': is_paired_field,
                     'paired': fields.List(fields.Nested(student_pairing_model))}
parent_pairing_info_form = {'is_paired': is_paired_field,
                            'paired': fields.List(fields.Nested(parent_pairing_model))}
student_pairing_info_model = UserNs.model('student_pairing_info', pairing_info_form)
parent_pairing_info_model = UserNs.model('parent_pairing_info', parent_pairing_info_form)

user_info_form = {'uid': uid_field,
                  'user_type': student_user_type_field,
                  'name': user_name_field,
                  'phone_number': phone_number_field,
                  'birthday': birthday_field,
                  'email': email_field,
                  'gender': gender_field,
                  'nickname': nickname_field,
                  'provider': provider_field,
                  'provider_id': provider_id_field,
                  'profile_numbering': profile_numbering_field}

student_user_info_from = dict(user_info_form,
                              **{'grade': grade_field,
                                 'school_info': fields.Nested(school_info_model),
                                 'pairing_info': fields.Nested(student_pairing_info_model)})

parent_user_info_form = dict(user_info_form,
                             **{'pairing_info': fields.Nested(parent_pairing_info_model)})

teacher_in_academy_es_info_form = {'teacher_id': uid_field,
                                   'teacher_name': teacher_name_field}
teacher_in_academy_es_info_model = SearchNs.model('teacher_in_academy_info', teacher_in_academy_es_info_form)

system_added_tag_form = {'tag_id': tag_id_field,
                         'tag_name': tag_name_filed}
system_added_tag_model = SearchNs.model('system_added_tag', system_added_tag_form)
tags_info_form = {'system_added_tags': fields.List(fields.Nested(system_added_tag_model)),
                  'user_added_tags': fields.List(tag_name_filed)}
tags_info_model = SearchNs.model('tags_info', tags_info_form)

academy_es_info_form = {'_id': uid_field,
                        'name': academy_name_field,
                        'subject_info': fields.List(fields.Nested(subject_info_model)),
                        'address_info': fields.Nested(address_info_model),
                        'tags': fields.Nested(tags_info_model),
                        'teacher_info': fields.List(fields.Nested(teacher_in_academy_es_info_model)),
                        'phone_number': phone_number_field,
                        'account_number': account_number_field,
                        'class_count': class_count_field}

class_tag_info_form = {'system_added_tags': fields.List(tag_name_filed),
                       'user_added_tags': fields.List(tag_name_filed)}
class_tag_info_model = SearchNs.model('class_tag_info', class_tag_info_form)

academy_in_teacher_es_info_form = {'academy_name': academy_name_field,
                                   'academy_id': uid_field}
academy_in_teacher_es_info_model = SearchNs.model('academy_in_teacher_es_info', academy_in_teacher_es_info_form)
teacher_es_info_form = {'_id': uid_field,
                        'name': user_name_field,
                        'introduction': introduction_field,
                        'description': teacher_description_field,
                        'subject_info': fields.List(fields.Nested(subject_info_model)),
                        'academy_info': fields.List(fields.Nested(academy_in_teacher_es_info_model)),
                        'phone_number': phone_number_field,
                        'account_number': account_number_field}

self_login_user_form = {'email': email_field, 'password': password_field}
sns_login_user_form = {'provider': provider_field, 'provider_id': provider_id_field}
issue_token_output_form = {'result': success_field,
                           'token': token_field}
uid_info_form = {'uid': uid_field}
phone_number_form = {'phone_number': phone_number_field}
email_info_form = {'email': email_field}
match_token_form = {'uid': uid_field,
                    'token': token_field}
select_paired_student_form = {'uid': uid_field, 'student_id': student_uid_field}

student_name_info_form = {'uid': student_uid_field,
                          'name': user_name_field}
student_name_info_model = UserNs.model('child_name_info', student_name_info_form)
success_login_token_form = {'jwt_token': jwt_token_field,
                            'user': fields.Nested(user_token_info_model)}

update_password_form = {'uid': uid_field,
                        'password': password_field}
update_user_info_form = {'uid': uid_field,
                         'name': user_name_field,
                         'nickname': nickname_field,
                         'phone_number': phone_number_field,
                         'birthday': birthday_field,
                         'gender': gender_field,
                         'school_code': school_code_field}

send_code_phone_number_form = {'phone_number': phone_number_field}
verify_code_phone_number_form = {'phone_number': phone_number_field,
                                 'code': code_field}
verify_code_forgot_email_output_form = dict({'email': email_field}, )
forgot_password_send_code_form = {'phone_number': phone_number_field,
                                  'email': email_field}
forgot_password_new_password_form = {'phone_number': phone_number_field,
                                     'password': password_field}

delete_user_form = {'uid': uid_field}
user_profile_upload_form = {'img_url': img_url_field,
                            'uid': uid_field}
user_profile_upload_output_form = {'profile_numbering': profile_numbering_field}

academy_search_condition_form = {'name': academy_name_field,
                                 'school_course': fields.List(school_course_field),
                                 'major_subject_id': fields.List(major_subject_id_field),
                                 'address_tag_id': tag_id_field,
                                 'tag_id': fields.List(tag_id_field),
                                 'sort': fields.List(sort_field)}

teacher_search_condition_form = {'school_course': fields.List(school_course_field),
                                 'major_subject_id': fields.List(major_subject_id_field),
                                 'tag_id': fields.List(tag_id_field)}

class_search_condition_form = {'name': class_name_field,
                               'academy_id': uid_field,
                               'teacher_id': uid_field,
                               'address_tag_id': tag_id_field,
                               'major_subject_id': major_subject_id_field,
                               'subject_id': fields.List(subject_id_field),
                               'school_course': school_course_field,
                               'grade': grade_field_str,
                               'week_day': fields.List(weekday_field),
                               'start': time_field,
                               'end': time_field,
                               'sort': fields.List(sort_field)}

school_search_condition_form = {'SCHUL_NM': school_name_search_field}

regular_schedule_query_form = {'student_id': student_uid_field,
                               'class_id': class_id_field,
                               'ignore_overlap': ignore_overlap_field}

regular_schedule_form = {'over_night': over_night_field,
                         'start': time_field,
                         'end': time_field,
                         'week_day': weekday_field}

regular_schedule_model = ClassNs.model('regular_schedule', regular_schedule_form)

schedule_and_class_common_info_form = {'subject_info': fields.Nested(subject_info_model),
                                       'academy_info': fields.Nested(academy_info_model),
                                       'teacher_info': fields.List(fields.Nested(teacher_info_model))}

base_class_info_model = ClassNs.model('base_class_info', schedule_and_class_common_info_form)

class_doc_info_form = dict({'name': class_name_field,
                            'created_date': date_field,
                            'start_date': date_field,
                            'end_date': date_field,
                            'closed': closed_class_field,
                            'regular_schedule': fields.List(fields.Nested(regular_schedule_model)),
                            'description': class_description_field,
                            'tags': fields.Nested(class_tag_info_model)},
                           **schedule_and_class_common_info_form)

class_info_with_id_form = dict({'_id': class_id_field}, **class_doc_info_form)

class_info_with_id_model = SearchNs.model('class_info_with_id', class_info_with_id_form)

class_update_form = dict({'class_id': class_id_field}, **class_doc_info_form)

schedule_form = dict({'class_id': class_id_field,
                      'schedule_id': schedule_id_field,
                      'name': class_name_field,
                      'description': class_description_field,
                      'class_info': fields.Nested(base_class_info_model),
                      'date': fields.Nested(date_model)},
                     **regular_schedule_form)

subject_form = {'subject_name': subject_name_field,
                'subject_id': subject_id_field,
                'belonged_subject': major_subject_id_field,
                'grade': grade_field}
tag_form = {'tag_id': tag_id_field,
            'tag_name': tag_name_filed}
address_tag_form = {'address_tag_id': tag_id_field,
                    'address_tag_name': address_tag_name_filed}

add_user_class_input_form = {'uid': uid_field,
                             'name': class_name_field,
                             'description': class_description_field,
                             'academy_name': academy_name_field,
                             'teacher_name': teacher_name_field,
                             'start_date': date_field,
                             'end_date': date_field,
                             'schedule_count': schedule_count_field,
                             '0_week_day': weekday_field,
                             '0_start': time_field,
                             '0_end': time_field}

delete_user_class_input_form = {'uid': uid_field,
                                'class_id': user_class_id_field}

add_schedule_input_form = {'year': year_field,
                           'month': month_field,
                           'day': day_field,
                           'uid': uid_field,
                           'start': time_field,
                           'end': time_field,
                           'name': class_name_field,
                           'academy_name': academy_name_field,
                           'teacher_name': teacher_name_field,
                           'description': memo_field,
                           'ignore_overlap': ignore_overlap_field}

update_schedule_input_form = {'uid': uid_field,
                              'schedule_id': schedule_id_field,
                              'description': memo_field,
                              'original_year': year_field,
                              'original_month': month_field,
                              'original_day': day_field,
                              'original_start': original_time_field,
                              'original_end': original_time_field,
                              'new_year': year_field,
                              'new_month': month_field,
                              'new_day': day_field,
                              'new_start': new_time_field,
                              'new_end': new_time_field,
                              'ignore_overlap': ignore_overlap_field}
update_schedule_output_form = {'schedule_id': schedule_id_field}
delete_schedule_input_form = {'year': year_field,
                              'month': month_field,
                              'student_id': student_uid_field,
                              'schedule_id': schedule_id_field,
                              'start': time_field,
                              'end': time_field,
                              'day': day_field}

email_check_form = {'email': email_field}

update_academy_form = {'name': academy_name_field,
                       'subject_info': fields.List(fields.Nested(subject_info_model)),
                       'address_info': fields.Nested(address_info_model),
                       'tags': fields.Nested(tags_info_model),
                       'teacher_info': fields.List(fields.Nested(teacher_info_model)),
                       'phone_number': phone_number_field,
                       'homepage_url': homepage_url_field,
                       'account_number': account_number_field}

update_teacher_form = {'name': teacher_name_field,
                       'subject_info': fields.List(fields.Nested(subject_info_model)),
                       'academy_info': fields.List(fields.Nested(academy_in_teacher_es_info_model)),
                       'tags': fields.Nested(tags_info_model),
                       'phone_number': phone_number_field,
                       'account_number': account_number_field}

schedule_model = ScheduleNs.model('schedule', schedule_form)
week_preview_schedule_class_form = {'monday_date': date_field,
                                    'schedule': fields.List(fields.Nested(schedule_model))}
month_preview_schedule_class_form = {'month': month_field,
                                     'year': year_field,
                                     'schedule': fields.List(fields.Nested(schedule_model))}

get_allclass_notice_form = {'doc_id': doc_id_field,
                            'title': title_field,
                            'content': content_field,
                            'created_time': date_field,
                            'images': fields.List(img_url_field),
                            'image_path': image_path_field}

## Academy
get_academy_notice_form = {'doc_id': doc_id_field,
                           'title': title_field,
                           'content': content_field,
                           'created_time': date_field,
                           'images': fields.List(img_url_field),
                           'image_path': image_path_field}
put_academy_notice_form = {'academy_id': uid_field,
                           'title': title_field,
                           'content': content_field,
                           'images': fields.List(img_url_field)}
update_academy_notice_form = {'doc_id': doc_id_field,
                              'academy_id': uid_field,
                              'title': title_field,
                              'content': content_field,
                              'images': fields.List(img_url_field)}
get_academy_notice_titles_form = {'title': title_field,
                                  'doc_id': doc_id_field,
                                  'created_time': date_field}
get_all_academy_notice_titles_form = {'title': title_field,
                                      'doc_id': doc_id_field,
                                      'academy_name': academy_name_field,
                                      'academy_id': uid_field,
                                      'created_time': date_field_2}

## Advertisement
get_random_advertisement_input_form = {'uid': uid_field, 'ad_location_id': ad_location_id_field}
get_random_advertisement_output_form = {'ad_id': ad_id_field,
                                        'image': image_name_field,
                                        'redirect_url': redirect_url_field,
                                        'image_path': image_path_field}

# ----- Swagger Model -----
## User
success_response_model = UserNs.model('success_response', success_response_form)
success_login_token_model = UserNs.model('success_login_token', success_login_token_form)
fail_response_model = UserNs.model('fail_response', fail_response_form)

get_academy_info_agree_model = _data_response_model(get_academy_info_agree_form, UserNs, 'get_academy_info_agree',
                                                    list_form=False)
update_academy_info_agree_model = UserNs.model('update_academy_info_agree', update_academy_info_agree_form)

sns_register_student_model = UserNs.model('sns_register_student', sns_student_user_form)
sns_register_parent_model = UserNs.model('sns_register_parent', sns_parent_user_form)

self_register_student_model = UserNs.model('self_register_student', self_student_user_form)
self_register_parent_model = UserNs.model('self_register_parent', self_parent_user_form)
self_register_academy_model = UserNs.model('self_register_academy', self_academy_user_form)
self_register_teacher_model = UserNs.model('self_register_teacher', self_teacher_user_form)

issue_token_output_model = UserNs.model('issue_token_output', issue_token_output_form)
uid_info_model = UserNs.model('uid_info', uid_info_form)
phone_number_model = UserNs.model('phone_number', phone_number_form)
match_token_model = UserNs.model('match_token', match_token_form)
select_paired_student_model = UserNs.model('select_paired_student', select_paired_student_form)

self_login_model = UserNs.model('self_login', self_login_user_form)
sns_login_model = UserNs.model('sns_login', sns_login_user_form)

student_user_info_model = _data_response_model(student_user_info_from, UserNs, 'student_user_info',
                                               list_form=False, data_key='user')
parent_user_info_model = _data_response_model(parent_user_info_form, UserNs, 'parent_user_info',
                                              list_form=False, data_key='user')
general_user_info_model = _data_response_model(user_info_form, UserNs, 'general_user_info',
                                               list_form=False, data_key='user')

email_check_model = UserNs.model('email_check_model', email_check_form)

update_password_model = UserNs.model('update_password', update_password_form)
update_user_info_model = UserNs.model('update_user_info', update_user_info_form)

send_code_phone_number_model = UserNs.model('send_code_phone_number', send_code_phone_number_form)
verify_code_model = UserNs.model('verify_code', verify_code_phone_number_form)
email_info_model = UserNs.model('email_info', email_info_form)
forgot_password_send_code_model = UserNs.model('forgot_password_send_code', forgot_password_send_code_form)
forgot_password_new_password_model = UserNs.model('forgot_password_new_password', forgot_password_new_password_form)

delete_user_model = UserNs.model('delete_user', delete_user_form)

user_profile_upload_model = UserNs.model('user_profile_upload', user_profile_upload_form)
user_profile_upload_output = UserNs.model('user_profile_upload_output', user_profile_upload_output_form)

update_academy_model = UserNs.model('update_academy', update_academy_form)
update_teacher_model = UserNs.model('update_teacher', update_teacher_form)

## Search
academy_search_conditions_input = SearchNs.model('academy_search_conditions', academy_search_condition_form)
academy_search_output = _data_response_model(academy_es_info_form, SearchNs, 'academy_search', list_form=False)
academy_search_outputs = _data_response_model(academy_es_info_form, SearchNs, 'academy_search',
                                              list_form=True, sort_result=True)

teacher_search_conditions_input = SearchNs.model('teacher_search_conditions', teacher_search_condition_form)
teacher_search_output = _data_response_model(teacher_es_info_form, SearchNs, 'teacher_search', list_form=False)
teacher_search_outputs = _data_response_model(teacher_es_info_form, SearchNs, 'teacher_search', list_form=True)

school_search_input = SearchNs.model('school_search_condition', school_search_condition_form)
school_search_output = _data_response_model(school_info_form, SearchNs, 'school_search', list_form=True)

class_register_input = SearchNs.model('class_register', class_doc_info_form)

class_update_input = SearchNs.model('class_update', class_update_form)

search_class_conditions_input = SearchNs.model('search_class_conditions', class_search_condition_form)
search_class_parameter = reqparse.RequestParser(). \
    add_argument('academy_id', type=str, default=None). \
    add_argument('teacher_id', type=str, default=None)

search_class_output = _data_response_model(class_info_with_id_form, SearchNs, 'search_class', list_form=True)
search_class_outputs = _data_response_model(class_info_with_id_form, SearchNs, 'search_classes',
                                            list_form=True, sort_result=True)

search_academy_parameter = reqparse.RequestParser(). \
    add_argument('academy_id', type=str, default=None)

search_teacher_parameter = reqparse.RequestParser(). \
    add_argument('teacher_id', type=str, default=None)

search_schedule_output = _data_response_model(schedule_form, SearchNs, 'search_schedule', list_form=True)

search_subject_parameter = reqparse.RequestParser(). \
    add_argument('belonged_subject', type=str, default=None). \
    add_argument('school_course', type=str, default=None). \
    add_argument('grade', type=str, default=None). \
    add_argument('subject_code', type=str, default=None)

search_belonged_subjects_model = _data_response_model(subject_form, SearchNs, 'subject', list_form=True)
search_tag_model = _data_response_model(tag_form, SearchNs, 'tag', list_form=True)
search_address_tag_model = _data_response_model(address_tag_form, SearchNs, 'tag', list_form=True)

## Schedule
regular_schedule_query_model = ScheduleNs.model('regular_schedule_query', regular_schedule_query_form)

get_schedule_parameter_model = reqparse.RequestParser(). \
    add_argument('student_id', type=str, default=None). \
    add_argument('time_level', type=str, default=None). \
    add_argument('year', type=str, default=None). \
    add_argument('month', type=str, default=None). \
    add_argument('day', type=str, default=None)

check_class_schedule_parameter_model = reqparse.RequestParser(). \
    add_argument('class_id', type=str, default=None). \
    add_argument('time_level', type=str, default=None). \
    add_argument('year', type=str, default=None). \
    add_argument('month', type=str, default=None). \
    add_argument('day', type=str, default=None)

get_class_parameter = reqparse.RequestParser(). \
    add_argument('class_id', type=str, default=None)
get_class_output = _data_response_model(class_info_with_id_form, ClassNs, 'get_class', list_form=False)

update_schedule_input_model = ScheduleNs.model('update_schedule_input', update_schedule_input_form)
update_schedule_output_model = ScheduleNs.model('update_schedule_output', update_schedule_output_form)
delete_schedule_input_model = ScheduleNs.model('delete_schedule_input', delete_schedule_input_form)
add_schedule_input_model = ScheduleNs.model('add_schedule_input', add_schedule_input_form)
add_user_class_input_model = ScheduleNs.model('add_user_class_input', add_user_class_input_form)
delete_user_class_input_model = ScheduleNs.model('delete_user_class_input', delete_user_class_input_form)

week_preview_schedule_class_model = _data_response_model(
    week_preview_schedule_class_form, ClassNs, 'week_preview_schedule_class')
month_preview_schedule_class_model = _data_response_model(
    month_preview_schedule_class_form, ClassNs, 'month_preview_schedule_class')

get_allclass_notice_parameter = reqparse.RequestParser().add_argument('doc_id', type=str, default=None)
get_allclass_notice_output = \
    _data_response_model(get_allclass_notice_form, UserNs, 'get_allclass_notice', list_form=False)

## Academy
get_academy_notice_parameter = reqparse.RequestParser(). \
    add_argument('doc_id', type=str, default=None). \
    add_argument('academy_id', type=str, default=None)
get_academy_notice_output = \
    _data_response_model(get_academy_notice_form, AcademyNs, 'get_academy_notice', list_form=False)
insert_academy_notice_model = AcademyNs.model('put_academy_notice', put_academy_notice_form)
update_academy_notice_model = AcademyNs.model('put_academy_notice', update_academy_notice_form)
get_academy_notice_titles_parameter = reqparse.RequestParser(). \
    add_argument('academy_id', type=str, default=None). \
    add_argument('count', type=int, default=None). \
    add_argument('offset', type=int, default=None)
get_academy_notice_titles_output = _data_response_model(get_academy_notice_titles_form, AcademyNs,
                                                        'get_academy_notice_titles_output', list_form=True)
get_all_academy_notice_titles_parameter = reqparse.RequestParser(). \
    add_argument('count', type=int, default=None). \
    add_argument('offset', type=int, default=None)
get_all_academy_notice_titles_output = _data_response_model(get_all_academy_notice_titles_form, AcademyNs,
                                                            'get_all_academy_notice_titles_output', list_form=True)

## Advertisement
get_random_advertisement_input = AdvertisementNs.model('get_random_advertisement_input',
                                                       get_random_advertisement_input_form)
get_random_advertisement_output = _data_response_model(get_random_advertisement_output_form, AdvertisementNs,
                                                       'get_random_advertisement', list_form=False)
