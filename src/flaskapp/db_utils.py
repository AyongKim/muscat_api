import uuid
import hashlib
from datetime import datetime, timedelta, date

import pymysql
from flask import g

from flaskapp.constants import *


def hashing_password(passwd):
    return hashlib.sha1(passwd.encode()).hexdigest()


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
        if var_tuple == ():
            query = base_query
        else:
            query = cursor.mogrify(base_query, var_tuple)

        cursor.execute(query)

        # select 일때만 값 return
        if return_flag:
            query_result = cursor.fetchall()
        else:
            database.commit()

        return query_result

def check_login(email, password):
    password = hashing_password(password)

    query = f'SELECT user_email, user_type, code, updated_time, user_id FROM {USER_TABLE} ' \
            f'WHERE user_email = %s AND user_password = %s '
    
    res = execute_query(query, (email, password))
    return res[0] if res else None

def check_duplication(email, nickname):
    query = f'SELECT * FROM {USER_TABLE} ' \
            f'WHERE user_email = %s OR nickname = %s '
    
    res = execute_query(query, (email, nickname))
    return res[0] if res else None

def register_user(data):
    nickname = data['nickname']
    user_email = data['user_email']
    user_password = hashing_password(data['user_password'])
    user_type = str(data['user_type'])
    register_num = data['register_num'] if 'register_num' in data else ''
    company_address = data['company_address'] if 'company_address' in data else ''
    manager_name = data['manager_name'] if 'manager_name' in data else ''
    manager_phone = data['manager_phone'] if 'manager_phone' in data else ''
    manager_depart = data['manager_depart'] if 'manager_depart' in data else ''
    manager_grade = data['manager_grade'] if 'manager_grade' in data else ''
    other = data['other'] if 'other' in data else ''
    approval = str(0)
    admin_name = data['admin_name'] if 'admin_name' in data else ''
    admin_phone = data['admin_phone'] if 'admin_phone' in data else ''

    query = f'INSERT INTO {USER_TABLE} (user_email, user_password, user_type, register_num, company_address, manager_name, manager_phone, manager_depart, manager_grade, other, approval, nickname, admin_name, admin_phone) '\
            f'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    execute_query(query, (user_email, user_password, user_type, register_num, company_address, manager_name, manager_phone, manager_depart, manager_grade, other, approval, nickname, admin_name, admin_phone))

def update_user(data):
    data_list = []
    update_list = []

    for k, v in data.items():
        if k in ['user_email', 'user_password', 'company_address', 'manager_name', 'manager_phone', 'manager_depart', 'manager_grade', 'other', 'approval', 'nickname', 'admin_name', 'admin_phone', 'code', 'updated_time', 'access_time']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE {USER_TABLE} SET {",".join(update_list)} WHERE user_id = %s'
        data_list.append(data['user_id'])
        execute_query(query, tuple(data_list))

def delete_user(str_ids):
    query = f'DELETE FROM {USER_TABLE} WHERE user_id in ({str_ids})'

    execute_query(query, ())

def user_check_id(id):
    query = f'SELECT * FROM {USER_TABLE} ' \
            f'WHERE nickname = "{id}"'
    
    res = execute_query(query, ())
    return res[0] if res else None

def get_user_list():
    query = f'SELECT * FROM {USER_TABLE}'

    data = execute_query(query, ())
    return data

def check_company_duplication(register_num):
    query = f'SELECT * FROM {COMPANY_TABLE} ' \
            f'WHERE register_num = %s'
    
    res = execute_query(query, (register_num))
    return res[0] if res else None

def register_company(data):
    register_num = data['register_num']
    company_name = data['company_name']

    query = f'INSERT INTO {COMPANY_TABLE} (register_num, company_name) '\
            f'VALUES (%s, %s)'
    execute_query(query, (register_num, company_name))

def update_company(data):
    data_list = []
    update_list = []

    for k, v in data.items():
        if k in ['register_num', 'company_name']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE {COMPANY_TABLE} SET {",".join(update_list)} WHERE id = %s'
        data_list.append(data['id'])
        execute_query(query, tuple(data_list))

def get_company_list():
    query = f'SELECT id, register_num, company_name FROM {COMPANY_TABLE}'

    data = execute_query(query, ())
    return data

def delete_company(str_ids):
    query = f'DELETE FROM {COMPANY_TABLE} WHERE id in ({str_ids})'

    execute_query(query, ())
    
def check_company(register_num):
    query = f'SELECT * FROM {COMPANY_TABLE} ' \
            f'WHERE register_num = %s'
    
    res = execute_query(query, (register_num))
    return res[0] if res else None

def company_check(register_num):
    query = f'SELECT company_name FROM {COMPANY_TABLE} ' \
            f'WHERE register_num = %s'
    
    res = execute_query(query, (register_num))
    return res[0] if res else None

def register_project(data):
    year = data['year']
    name = data['name']
    user_id = data['user_id']
    checklist_id = data['checklist_id']
    privacy_type = data['privacy_type']

    today = datetime.now().strftime('%Y-%m-%d')
    query = f'INSERT INTO {PROJECT_TABLE} (year, name, user_id, checklist_id, privacy_type, created_date, create_from, create_to, self_check_from, self_check_to, imp_check_from, imp_check_to) '\
            f'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    execute_query(query, (year, name, user_id, checklist_id, privacy_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), today, today, today, today, today, today))

def update_project_schedule(data):
    data_list = []
    update_list = []

    for k, v in data.items():
        if k in ['create_from', 'create_to', 'self_check_from', 'self_check_to', 'imp_check_from', 'imp_check_to']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE {PROJECT_TABLE} SET {",".join(update_list)} WHERE id = %s'
        data_list.append(data['id'])
        execute_query(query, tuple(data_list))

def get_project_schedule(id):
    query = f'SELECT create_from, create_to, self_check_from, self_check_to, imp_check_from, imp_check_to FROM {PROJECT_TABLE} ' \
            f'WHERE id = %s'
    
    res = execute_query(query, (id))
    return res[0] if res else None

def get_project_list():
    query = f'SELECT id, year, name, user_id, checklist_id, privacy_type FROM {PROJECT_TABLE}'

    data = execute_query(query, ())
    return data

def register_notice(data):
    project_id = data['project_id']
    title = data['title']
    content = data['content']
    create_by = data['create_by']
    create_time = data['create_time']
    views = data['views']
    attachment = data['attachment']

    query = f'INSERT INTO {NOTICE_TABLE} (project_id, title, content, create_by, create_time, views, attachment) '\
            f'VALUES (%s, %s, %s, %s, %s, %s, %s)'
    execute_query(query, (project_id, title, content, create_by, create_time, views, attachment))
    
def get_notice_attachment(id):
    query = f'SELECT create_time, attachment FROM {NOTICE_TABLE} ' \
            f'WHERE id = %s'
    
    res = execute_query(query, (id))
    return res[0] if res else None

def update_notice(data):
    data_list = []
    update_list = []

    for k, v in data.items():
        if k in ['project_id', 'title', 'content', 'attachment']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE {PROJECT_TABLE} SET {",".join(update_list)} WHERE id = %s'
        data_list.append(data['id'])
        execute_query(query, tuple(data_list))

def get_notice_list():
    query = f'SELECT A.id, B.name, A.create_by, A.create_time, A.views FROM {NOTICE_TABLE} as A LEFT JOIN project as B ON A.project_id=B.id'

    data = execute_query(query, ())
    return data

def delete_notice(str_ids):
    query = f'DELETE FROM {NOTICE_TABLE} WHERE id in ({str_ids})'

    execute_query(query, ())