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
        query = cursor.mogrify(base_query, var_tuple)
        print(query)
        cursor.execute(query)

        # select 일때만 값 return
        if return_flag:
            query_result = cursor.fetchall()
        else:
            database.commit()

        return query_result

def check_login(email, password):
    password = hashing_password(password)

    query = f'SELECT user_email, user_type, code, updated_time, user_id FROM user ' \
            f'WHERE user_email = %s AND user_password = %s '
    
    res = execute_query(query, (email, password))
    return res[0] if res else None

def check_duplication(email, nickname):
    query = f'SELECT * FROM user ' \
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

    query = f'INSERT INTO user (user_email, user_password, user_type, register_num, company_address, manager_name, manager_phone, manager_depart, manager_grade, other, approval, nickname, admin_name, admin_phone) '\
            f'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    execute_query(query, (user_email, user_password, user_type, register_num, company_address, manager_name, manager_phone, manager_depart, manager_grade, other, approval, nickname, admin_name, admin_phone))

def update_user(data):
    data_list = []
    update_list = []

    for k, v in data.items():
        if k in ['user_email', 'user_password', 'company_address', 'manager_name', 'manager_phone', 'manager_depart', 'manager_grade', 'other', 'approval', 'nickname', 'admin_name', 'admin_phone', 'code', 'updated_time']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE user SET {",".join(update_list)} WHERE user_id = %s'
        data_list.append(data['user_id'])
        execute_query(query, tuple(data_list))

def check_company_duplication(register_num):
    query = f'SELECT * FROM company ' \
            f'WHERE register_num = %s'
    
    res = execute_query(query, (register_num))
    return res[0] if res else None

def register_company(data):
    register_num = data['register_num'] if data['register_num'] else ''
    company_name = data['company_name'] if data['company_name'] else ''

    query = f'INSERT INTO company (register_num, company_name) '\
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
        query = f'UPDATE company SET {",".join(update_list)} WHERE id = %s'
        data_list.append(data['id'])
        execute_query(query, tuple(data_list))
