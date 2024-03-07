import uuid
import hashlib
from datetime import datetime, timedelta, date

import pymysql
from flask import g

from flaskapp.constants import *
from flaskapp.enums import UserCode, LoginProvider, FailResponse


def hashing_password(passwd):
    return hashlib.sha256(passwd.encode()).hexdigest()


def _connect_db():
    conn = pymysql.connect(
        user=DB_USER,
        passwd=DB_PASSWORD,
        database=ALL_CLASS_DB,
        host=DB_ENDPOINT,
        port=DB_PROT,
        charset='utf8'
    )
    return conn


def get_db():
    if 'db' not in g:
        g.db = _connect_db()
    return g.db


def execute_query(base_query: str, var_tuple: tuple):
    database = get_db()
    return_flag = base_query.startswith('SELECT') or base_query.startswith('SHOW')
    query_result = None

    with database.cursor() as cursor:
        query = cursor.mogrify(base_query, var_tuple)
        cursor.execute(query)

        # select 일때만 값 return
        if return_flag:
            query_result = cursor.fetchall()
        else:
            database.commit()

        return query_result


def insert_login_token(login_token, refresh_token, nbf_time):
    query = f'INSERT INTO {LOGIN_TOKEN_TABLE} (token, refresh_token, nbf_time) VALUES (%s, %s, %s)'
    execute_query(query, (login_token, refresh_token, nbf_time))


def get_refresh_token(login_token):
    query = f'SELECT refresh_token FROM {LOGIN_TOKEN_TABLE} WHERE token = %s'
    res = execute_query(query, (login_token,))
    return res[0][0] if res else None


def delete_login_token(token):
    query = f'DELETE FROM {LOGIN_TOKEN_TABLE} WHERE token = %s'
    execute_query(query, (token,))


def soft_delete_user(uid):
    query = f'UPDATE {USER_TABLE} SET active = %s WHERE uid = %s'
    execute_query(query, (0, uid))


def hard_delete_user(uid):
    query = f'DELETE FROM {USER_TABLE} WHERE uid = %s'
    execute_query(query, (uid,))


def check_password(e_mail, passwd):
    passwd = hashing_password(passwd)
    query = f'SELECT uid, active FROM {USER_TABLE} ' \
            f'WHERE email = %s AND uid IN (SELECT uid FROM {PASSWORD_TABLE} WHERE password = %s)'
    res = execute_query(query, (e_mail, passwd))
    return res[0] if res else None


def get_user_info_by_nickname(nickname):
    query = f'SELECT * FROM {USER_TABLE} WHERE nickname = %s'
    res = execute_query(query, (nickname,))
    return res[0] if res else None


def get_user_info_by_phone_number(phone_number):
    query = f'SELECT * FROM {USER_TABLE} WHERE phone_number = %s'
    res = execute_query(query, (phone_number,))
    return res[0] if res else None


def get_user_uid_and_email_by_phone_number(phone_number):
    query = f'SELECT uid, email FROM {USER_TABLE} WHERE phone_number = %s'
    res = execute_query(query, (phone_number,))
    # TODO : 같은 phone number 로 여러 개의 계정이 있을 경우 핸들링
    return res[0] if res else None


def get_user_info_by_uid(uid):
    query = f'SELECT uid, user_type, name, phone_number, birthday, email, gender, nickname, provider, ' \
            f'provider_id, active, profile_numbering FROM {USER_TABLE} WHERE uid = %s'

    res = execute_query(query, (uid,))
    return res[0] if res else None


def get_user_info_by_email(e_mail):
    query = f'SELECT * FROM {USER_TABLE} WHERE email = %s'
    res = execute_query(query, (e_mail,))
    return res[0] if res else None


def get_user_info_by_provider(provider, provider_id):
    query = f'SELECT uid, user_type, name, phone_number, birthday, email, gender, nickname, provider, ' \
            f'provider_id, active, profile_numbering FROM {USER_TABLE} WHERE (provider, provider_id) = (%s, %s)'
    res = execute_query(query, (provider, provider_id))
    return res[0] if res else None


def get_students_info_of_parent(parent_id):
    query = f'SELECT p.uid, p.name, q.selected FROM {USER_TABLE} AS p JOIN ' \
            f'(SELECT student_id, selected FROM {PAIRING_TABLE} WHERE (parent_id, token) = (%s, %s)) AS q ' \
            f'ON p.uid = q.student_id'

    res = execute_query(query, (parent_id, MATCHED_VALUE))
    return res if res else ()


def get_paired_students_info_of_parent(parent_id):
    students_info = []

    student_results = get_students_info_of_parent(parent_id=parent_id)
    for student_result in student_results:
        students_info.append(
            {'uid': student_result[0], 'name': student_result[1], 'selected': student_result[2] == SELECTED})

    return students_info


def get_parents_info_of_student(student_id):
    query = f'SELECT uid, user_type, name, phone_number, birthday, email, gender, nickname, provider, ' \
            f'provider_id, active, profile_numbering FROM {USER_TABLE} WHERE uid IN ' \
            f'(SELECT parent_id FROM {PAIRING_TABLE} WHERE (student_id, token) = (%s, %s))'
    res = execute_query(query, (student_id, MATCHED_VALUE))
    return res if res else ()


def save_academy_info_agree(uid, get_academy_info):
    query = f'UPDATE {AGREE_TABLE} SET get_academy_info = %s WHERE uid = %s'
    execute_query(query, (get_academy_info, uid))


def get_academy_info_agree(uid):
    query = f'SELECT get_academy_info FROM {AGREE_TABLE} WHERE uid = %s'
    res = execute_query(query, (uid,))
    return res[0][0] if res else None


def save_agree_info(uid, get_academy_info, provide_personal_info):
    query = f'INSERT INTO {AGREE_TABLE} (uid, get_academy_info, provide_personal_info) VALUES (%s, %s, %s)'
    execute_query(query, (uid, get_academy_info, provide_personal_info))


def save_school_code(student_id, school_code):
    student_info_update_query = f'UPDATE {STUDENT_TABLE} SET school_code = %s WHERE student_id = %s'
    execute_query(student_info_update_query, (school_code, student_id))


def register_student_user_sns(user_data):
    student_id = str(uuid.uuid4())
    save_sns_register_student_info(student_id=student_id, name=user_data[NAME], phone_number=user_data[PHONE_NUMBER],
                                   nickname=user_data[NICKNAME], birthday=user_data[BIRTHDAY], gender=user_data[GENDER],
                                   provider_id=user_data[PROVIDER_ID],  provider=user_data[PROVIDER])
    save_school_code(student_id=student_id, school_code=user_data['school_code'])
    save_agree_info(uid=student_id,
                    get_academy_info=user_data['get_academy_info'],
                    provide_personal_info=user_data['provide_personal_info'])
    return student_id


def save_sns_register_student_info(student_id, name, phone_number, nickname, provider, provider_id, birthday, gender):
    insert_user_info(uid=student_id, user_type=UserCode.STUDENT.value, name=name, nickname=nickname,
                     provider=provider, provider_id=provider_id, phone_number=phone_number, birthday=birthday,
                     gender=gender)

    insert_student_table_query = f'INSERT INTO {STUDENT_TABLE} (student_id) VALUES  (%s)'
    execute_query(insert_student_table_query, (student_id,))


def register_student_user_self(user_data: dict):
    student_id = str(uuid.uuid4())
    save_self_register_student_info(student_id=student_id, name=user_data[NAME], phone_number=user_data[PHONE_NUMBER],
                                    e_mail=user_data[EMAIL], nickname=user_data[NICKNAME], birthday=user_data[BIRTHDAY],
                                    gender=user_data[GENDER])
    save_school_code(student_id=student_id, school_code=user_data['school_code'])
    insert_password_of_user(student_id, user_data[PASSWORD])
    save_agree_info(uid=student_id,
                    get_academy_info=user_data['get_academy_info'],
                    provide_personal_info=user_data['provide_personal_info'])
    return student_id


def save_self_register_student_info(student_id, name, phone_number, e_mail, nickname, birthday, gender):
    insert_user_info(uid=student_id, user_type=UserCode.STUDENT.value, name=name, nickname=nickname,
                     provider=LoginProvider.SELF.value, phone_number=phone_number, email=e_mail,
                     birthday=birthday, gender=gender)

    insert_student_table_query = f'INSERT INTO {STUDENT_TABLE} (student_id) VALUES  (%s)'
    execute_query(insert_student_table_query, (student_id,))


def get_student_info(student_id):
    query = f'SELECT grade, school_code FROM {STUDENT_TABLE} WHERE student_id = %s'
    res = execute_query(query, (student_id,))
    return res[0] if res else None


def get_school_info(school_code):
    query = f'SELECT code, name, address FROM {SCHOOL_TABLE} WHERE code = %s'
    res = execute_query(query, (school_code,))
    return res[0] if res else None


def register_parent_user_sns(user_data):
    parent_id = str(uuid.uuid4())

    insert_user_info(uid=parent_id, user_type=UserCode.PARENT.value, name=user_data[NAME],
                     provider=user_data[PROVIDER], provider_id=user_data[PROVIDER_ID], nickname=user_data[NICKNAME],
                     phone_number=user_data[PHONE_NUMBER], birthday=user_data[BIRTHDAY], gender=user_data[GENDER])

    save_agree_info(uid=parent_id,
                    get_academy_info=user_data['get_academy_info'],
                    provide_personal_info=user_data['provide_personal_info'])
    return parent_id


def register_parent_user_self(user_data: dict):
    parent_id = str(uuid.uuid4())

    # insert parent info
    insert_user_info(uid=parent_id, user_type=UserCode.PARENT.value, name=user_data[NAME],
                     provider=LoginProvider.SELF.value, nickname=user_data[NICKNAME], email=user_data[EMAIL],
                     phone_number=user_data[PHONE_NUMBER], birthday=user_data[BIRTHDAY], gender=user_data[GENDER])

    # insert password
    passwd = user_data[PASSWORD]
    insert_password_of_user(parent_id, passwd)

    save_agree_info(uid=parent_id,
                    get_academy_info=user_data['get_academy_info'],
                    provide_personal_info=user_data['provide_personal_info'])
    return parent_id


def register_academy_user_info_self(user_data: dict):
    academy_id = str(uuid.uuid4())

    insert_user_info(uid=academy_id, user_type=UserCode.ACADEMY.value, name=user_data[NAME], nickname=user_data[NAME],
                     provider=LoginProvider.SELF.value, phone_number=user_data[PHONE_NUMBER], email=user_data[EMAIL])

    # insert password
    passwd = user_data[PASSWORD]
    insert_password_of_user(academy_id, passwd)
    return academy_id


def register_teacher_user_info_self(user_data: dict):
    teacher_id = str(uuid.uuid4())

    insert_user_info(uid=teacher_id, user_type=UserCode.TEACHER.value, name=user_data[NAME],
                     nickname=user_data[NAME], provider=LoginProvider.SELF.value, birthday=user_data[BIRTHDAY],
                     phone_number=user_data[PHONE_NUMBER], email=user_data[EMAIL], gender=user_data[GENDER])

    # insert password
    passwd = user_data[PASSWORD]
    insert_password_of_user(teacher_id, passwd)
    return teacher_id


def insert_user_info(uid, user_type, name, nickname, provider, provider_id=None, phone_number=None, birthday=None,
                     email=None, gender=None):

    query = f'INSERT INTO {USER_TABLE} ' \
            f'(uid, user_type, name, phone_number, birthday, email, gender, nickname, provider, provider_id) ' \
            f'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    execute_query(query, (uid, user_type, name, phone_number, birthday, email, gender, nickname, provider, provider_id))


def update_user_info(uid, **kwargs):
    data_list = []
    update_list = []

    if PHONE_NUMBER in kwargs:
        verify_phone_number_query = f'SELECT * FROM {VERIFY_PHONE_NUMBER} WHERE (phone_number, verified) = (%s, %s)'
        verify_result = execute_query(verify_phone_number_query, (kwargs[PHONE_NUMBER], 1))
        if len(verify_result) == 0:
            return FailResponse.UNVERIFIED_PHONE_NUMBER

    if 'school_code' in kwargs:
        update_school_query = f'UPDATE {STUDENT_TABLE} SET school_code = %s WHERE student_id = %s'
        execute_query(update_school_query, (kwargs['school_code'], uid))

    for k, v in kwargs.items():
        if k in [NICKNAME, BIRTHDAY, GENDER, PHONE_NUMBER, NAME] and v != '':
            update_list.append(f'{k} = %s')
            data_list.append(v)

    query = f'UPDATE {USER_TABLE} SET {",".join(update_list)} WHERE uid = %s'
    data_list.append(uid)
    execute_query(query, tuple(data_list))
    return SUCCESS_RESPONSE


def insert_password_of_user(uid, passwd):
    passwd = hashing_password(passwd)
    insert_password_query = f'INSERT INTO {PASSWORD_TABLE} (uid, password) VALUES (%s, %s)'
    execute_query(insert_password_query, (uid, passwd))


def update_password_of_user(uid, passwd, verify_number=None):
    passwd = hashing_password(passwd)
    insert_password_query = f'UPDATE {PASSWORD_TABLE} SET password = %s WHERE uid = %s'
    execute_query(insert_password_query, (passwd, uid))

    if verify_number:
        delete_verify_query = f'DELETE FROM {VERIFY_PHONE_NUMBER} WHERE verify_number = %s'
        execute_query(delete_verify_query, (verify_number,))


def insert_pairing_token_of_parent(parent_id, pairing_token):
    query = f'INSERT INTO {PAIRING_TABLE} (parent_id, student_id, token) VALUES (%s, %s, %s)'
    execute_query(query, (parent_id, NOT_MATCHED_VALUE, pairing_token))


def get_pairing_token_of_parent(parent_id):
    query = f'SELECT token FROM {PAIRING_TABLE} WHERE (parent_id, student_id) = (%s, %s)'
    res = execute_query(query, (parent_id, NOT_MATCHED_VALUE))
    return res[0] if res else None


def match_pairing_token(student_id, pairing_token):
    token_valid_query = f'SELECT pairing_number, parent_id FROM {PAIRING_TABLE} WHERE (token, student_id) = (%s, %s)'
    token_result = execute_query(token_valid_query, (pairing_token, NOT_MATCHED_VALUE))
    if not token_result or len(token_result) > 1:
        return FailResponse.INVALID_TOKEN

    pairing_number = token_result[0][0]
    parent_id = token_result[0][1]

    paired_check_query = f'SELECT * FROM {PAIRING_TABLE} WHERE (parent_id, token) = (%s, %s)'
    paired_check_result = execute_query(paired_check_query, (parent_id, MATCHED_VALUE))
    if len(paired_check_result) == 0:
        # 첫 매칭일 경우, current pairing 으로 지정
        selected = SELECTED
    else:
        selected = NOT_SELECTED

    pairing_query = f'UPDATE {PAIRING_TABLE} SET student_id = %s, token = %s, selected = %s WHERE pairing_number = %s'
    execute_query(pairing_query, (student_id, MATCHED_VALUE, selected, pairing_number))
    return SUCCESS_RESPONSE


def select_paired_student(parent_id, student_id):
    select_query = f'SELECT student_id FROM {PAIRING_TABLE} WHERE (parent_id, selected) = (%s, %s)'
    res = execute_query(select_query, (parent_id, SELECTED))
    if len(res) == 1:
        current_selected_student_id = res[0][0]
        if student_id == current_selected_student_id:
            return
        update_query = f'UPDATE {PAIRING_TABLE} SET selected = %s WHERE (parent_id, student_id) = (%s, %s)'
        execute_query(update_query, (SELECTED, parent_id, student_id))
        execute_query(update_query, (NOT_SELECTED, parent_id, current_selected_student_id))
    else:
        raise Exception(f'Selected student for {parent_id} is not 1: {len(res)}')


def delete_token_and_temp_student_info(parent_id, token):
    delete_token_query = f'DELETE FROM {PAIRING_TABLE} WHERE (parent_id, token) = (%s, %s)'
    execute_query(delete_token_query, (parent_id, token))

    delete_temp_student_query = f'DELETE FROM {TEMP_STUDENT_TABLE} WHERE parent_id = %s'
    execute_query(delete_temp_student_query, (parent_id,))


def get_subject_by_belonged_subject_and_school_course(belonged_subject, school_course=None):
    query = f'SELECT subject_id, subject_name, belonged_subject, grade FROM {SUBJECT_TABLE} ' \
            f'WHERE belonged_subject = %s ORDER BY CAST(subject_id AS unsigned)'

    if school_course:
        school_query_list = []
        for course in school_course:
            if course in SCHOOL_COURSES:
                school_query_list.append(f'{course} = 1')
        if len(school_query_list) > 0:
            query += f' AND ({" OR ".join(school_query_list)})'

    res = execute_query(query, (belonged_subject,))
    return res


def get_subject(subject_code):
    query = f'SELECT subject_id, subject_name, belonged_subject, grade FROM {SUBJECT_TABLE} WHERE subject_id = %s'
    res = execute_query(query, (subject_code,))
    return res[0] if res else None


def get_all_tags():
    query = f'SELECT tag_id, tag_name FROM {TAG_TABLE}'
    res = execute_query(query, ())
    tags = [{'tag_id': str(tag[0]), 'tag_name': tag[1]} for tag in res]
    return tags


def get_tag(tag_id):
    query = f'SELECT tag_id, tag_name FROM {TAG_TABLE} WHERE tag_id = %s'
    res = execute_query(query, (tag_id,))
    tags = [{'tag_id': str(tag[0]), 'tag_name': tag[1]} for tag in res]
    return tags


def get_all_address_tags():
    query = f'SELECT address_tag_id, address_tag_name FROM {ADDRESS_TAG_TABLE}'
    res = execute_query(query, ())
    tags = [{'address_tag_id': str(tag[0]), 'address_tag_name': tag[1]} for tag in res]
    return tags


def get_address_tag(tag_id):
    query = f'SELECT address_tag_id, address_tag_name FROM {ADDRESS_TAG_TABLE} WHERE address_tag_id = %s'
    res = execute_query(query, (tag_id,))
    tags = [{'address_tag_id': str(tag[0]), 'address_tag_name': tag[1]} for tag in res]
    return tags


def save_code_for_verifying_phone_number(phone_number, code, purpose):
    query = f'INSERT INTO {VERIFY_PHONE_NUMBER} (code, phone_number, created_time, purpose) VALUES (%s, %s, %s, %s)'
    now = datetime.now()
    execute_query(query, (code, phone_number, now, purpose))


def verify_code_for_phone_number(phone_number, code, purpose):
    query = f'SELECT created_time FROM {VERIFY_PHONE_NUMBER} WHERE (phone_number, code, verified, purpose) = ' \
            f'(%s, %s, %s, %s)'
    res = execute_query(query, (phone_number, code, 0, purpose))
    if res:
        created_time: datetime = res[0][0]
        now = datetime.now()

        if created_time + timedelta(minutes=5) < now:
            delete_query = f'DELETE FROM {VERIFY_PHONE_NUMBER} WHERE (phone_number, code) = (%s, %s)'
            execute_query(delete_query, (phone_number, code))
            return FailResponse.EXPIRED_CODE
        else:
            update_query = f'UPDATE {VERIFY_PHONE_NUMBER} SET verified = %s WHERE (phone_number, code) = (%s, %s)'
            execute_query(update_query, ('1', phone_number, code))
            return SUCCESS_RESPONSE

    else:
        return FailResponse.INVALID_CODE


def verify_password_change(phone_number):
    query = f'SELECT verify_number FROM {VERIFY_PHONE_NUMBER} WHERE (phone_number, verified, purpose) = (%s, %s, %s)'
    res = execute_query(query, (phone_number, 1, 'password'))
    return res[0] if res else None


def update_user_profile_numbering(uid, profile_numbering):
    query = f'UPDATE {USER_TABLE} SET profile_numbering = %s WHERE uid = %s'
    execute_query(query, (profile_numbering, uid))


def insert_academy_notice(notice_table, academy_id, title, content, image_count, created_time):
    query = f'INSERT INTO {notice_table} ' \
            f'(academy_id, title, content, image_count, created_time, modified_time) VALUES ' \
            f'(%s, %s, %s, %s, %s, %s)'
    execute_query(query, (academy_id, title, content, image_count, created_time, created_time))


def get_academy_notice(notice_table, doc_id, academy_id):
    query = f'SELECT title, content, image_start_num, image_count, created_time FROM {notice_table} ' \
            f'WHERE (doc_id, academy_id) = (%s, %s)'
    res = execute_query(query, (doc_id, academy_id))
    return res[0] if res else None


def update_academy_notice(notice_table, doc_id, academy_id, title, content, image_start_num, image_count, modified_time):
    query = f'UPDATE {notice_table} SET title = %s, content = %s, image_start_num = %s, ' \
            f'image_count = %s, modified_time = %s WHERE (doc_id, academy_id) = (%s, %s)'
    execute_query(query, (title, content, image_start_num, image_count, modified_time, doc_id, academy_id))


def get_recent_academy_notices(count, doc_id=None):
    data_list = []

    sub_query = f'SELECT doc_id, title, academy_id, created_time FROM {ACADEMY_NOTICE_TABLE} '
    if doc_id:
        sub_query += ' WHERE doc_id < %s '
        data_list.append(doc_id)

    sub_query += ' ORDER BY doc_id DESC '

    if count:
        sub_query += ' LIMIT %s '
        data_list.append(count)

    query = f'SELECT p.doc_id, p.title, q.name, q.uid, date_format(p.created_time, "%%Y.%%m.%%d") FROM ({sub_query}) AS p JOIN {USER_TABLE} AS q ON p.academy_id = q.uid '

    res = execute_query(query, tuple(data_list))
    return res


def get_titles_of_academy_notice(notice_table, academy_id, doc_id=None, count=None):
    query = f'SELECT doc_id, title, created_time FROM {notice_table} WHERE academy_id = %s '
    data_list = [academy_id]

    if doc_id:
        query += ' AND doc_id < %s '
        data_list.append(doc_id)

    query += ' ORDER BY doc_id DESC '

    if count:
        query += 'LIMIT %s '
        data_list.append(count)

    return execute_query(query, tuple(data_list))


def insert_allclass_notice(title, content, image_count, created_time):
    query = f'INSERT INTO {ALLCLASS_NOTICE_TABLE} ' \
            f'(title, content, image_count, created_time, modified_time) VALUES (%s, %s, %s, %s, %s)'
    execute_query(query, (title, content, image_count, created_time, created_time))


def get_allclass_notice(doc_id):
    query = f'SELECT title, content, image_start_num, image_count, created_time FROM {ALLCLASS_NOTICE_TABLE} ' \
            f'WHERE doc_id = %s'
    res = execute_query(query, (doc_id,))
    return res[0] if res else None


def update_allclass_notice(doc_id, title, content, image_start_num, image_count, modified_time):
    query = f'UPDATE {ALLCLASS_NOTICE_TABLE} SET title = %s, content = %s, image_start_num = %s, ' \
            f'image_count = %s, modified_time = %s WHERE doc_id = %s'
    execute_query(query, (title, content, image_start_num, image_count, modified_time, doc_id))


def get_titles_of_allclass_notice(doc_id=None, count=None):
    query = f'SELECT doc_id, title, created_time FROM {ALLCLASS_NOTICE_TABLE} '
    data_list = []

    if doc_id:
        query += 'WHERE doc_id < %s '
        data_list.append(doc_id)

    query += ' ORDER BY doc_id DESC '

    if count:
        query += 'LIMIT %s '
        data_list.append(count)

    return execute_query(query, tuple(data_list))


def insert_banner_advertisement(ad_location_id, image, redirect_url, description, created_time):
    query = f'INSERT INTO {ADVERTISEMENT_TABLE} ' \
            f'(ad_location_id, image, redirect_url, description, created_time, modified_time) ' \
            f'VALUES (%s, %s, %s, %s, %s, %s)'
    execute_query(query, (ad_location_id, image, redirect_url, description, created_time, created_time))


def get_random_banner_advertisement_image_and_ad_id(ad_location_id):
    query = f'SELECT ad_id, image, redirect_url FROM {ADVERTISEMENT_TABLE} ' \
            f'WHERE ad_location_id = %s ORDER BY RAND() LIMIT 1'
    res = execute_query(query, (ad_location_id,))
    return res[0] if res else None


def get_banner_advertisement(ad_id):
    query = f'SELECT ad_location_id, image, redirect_url, description FROM {ADVERTISEMENT_TABLE} WHERE ad_id = %s'
    res = execute_query(query, (ad_id,))
    return res[0] if res else None


def update_banner_advertisement(ad_id, image, redirect_url, description, modified_time):
    query = f'UPDATE {ADVERTISEMENT_TABLE} ' \
            f'SET image = %s, redirect_url = %s, description = %s, modified_time = %s WHERE ad_id = %s'
    execute_query(query, (image, redirect_url, description, modified_time, ad_id))


def get_all_banner_advertisement():
    query = f'SELECT ad_id, description, ad_location_id FROM {ADVERTISEMENT_TABLE}'
    res = execute_query(query, ())
    return res if res else []


class User(object):
    def __init__(self,
                 uid=None,
                 user_type=None,
                 name=None,
                 phone_number=None,
                 birthday=None,
                 email=None,
                 gender=None,
                 nickname=None,
                 provider=None,
                 provider_id=None,
                 active=None,
                 profile_numbering=None
                 ):
        self.uid = uid
        self.user_type = user_type
        self.name = name
        self.phone_number = phone_number
        self.birthday = birthday
        self.email = email
        self.gender = gender
        self.nickname = nickname
        self.provider = provider
        self.provider_id = provider_id
        self.active = active
        self.profile_numbering = profile_numbering

    def to_dict(self):
        result = self.__dict__
        if isinstance(result['birthday'], date):
            result['birthday'] = result['birthday'].strftime(DATE_FORMAT)
        return result

    @classmethod
    def from_db_result(cls, db_result):
        user = User()

        user.uid = db_result[0]
        user.user_type = db_result[1]
        user.name = db_result[2]
        user.phone_number = db_result[3]
        user.birthday = db_result[4]
        user.email = db_result[5]
        user.gender = db_result[6]
        user.nickname = db_result[7]
        user.provider = db_result[8]
        user.provider_id = db_result[9]
        user.active = db_result[10]
        user.profile_numbering = db_result[11]
        return user

    @classmethod
    def from_uid(cls, uid):
        db_result = get_user_info_by_uid(uid)
        return User.from_db_result(db_result) if db_result else User()
