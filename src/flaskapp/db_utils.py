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
        charset='utf8mb4'
    )
    return conn


def get_db():
    if 'db' not in g:
        g.db = _connect_db()
    return g.db


def execute_query(base_query: str, var_tuple: tuple):
    database = get_db()
    return_flag = base_query.startswith('SELECT') or base_query.startswith('SHOW')
    insert_flag = base_query.startswith('INSERT')
    query_result = None

    with database.cursor() as cursor:
        if var_tuple == ():
            query = base_query
        else:
            query = cursor.mogrify(base_query, var_tuple)

        cursor.execute(query)

        insert_id = cursor.lastrowid

        # select 일때만 값 return
        if return_flag:
            query_result = cursor.fetchall()
        else:
            database.commit()

        if insert_flag:
            return insert_id
        else:
            return query_result

def check_login(email):
    query = f'SELECT user_email, user_type, code, updated_time, user_id, admin_name, nickname, user_password, try_count, lock_time, approval FROM {USER_TABLE} ' \
            f'WHERE user_email = %s'
    
    res = execute_query(query, (email))
    return res[0] if res else None

def check_duplication(email, nickname):
    query = f'SELECT * FROM {USER_TABLE} ' \
            f'WHERE user_email = %s OR nickname = %s '
    
    res = execute_query(query, (email, nickname))
    return res[0] if res else None

def check_email_duplication_with_id(email, id):
    query = f'SELECT * FROM {USER_TABLE} ' \
            f'WHERE user_email = %s AND user_id != %s '
    
    res = execute_query(query, (email, str(id)))
    return res[0] if res else None

def register_user(data):
    nickname = data['id']
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
    approval = data['approval'] if 'approval' in data else ''
    admin_name = data['admin_name'] if 'admin_name' in data else ''
    admin_phone = data['admin_phone'] if 'admin_phone' in data else ''

    query = f'INSERT INTO {USER_TABLE} (user_email, user_password, user_type, register_num, company_address, manager_name, manager_phone, manager_depart, manager_grade, other, approval, nickname, admin_name, admin_phone) '\
            f'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    
    return execute_query(query, (user_email, user_password, user_type, register_num, company_address, manager_name, manager_phone, manager_depart, manager_grade, other, approval, nickname, admin_name, admin_phone))

def update_user(data):
    data_list = []
    update_list = []

    if 'user_password' in data:
        data['user_password'] = hashing_password(data['user_password'])

    print(data)
    for k, v in data.items():
        if k in ['user_email', 'user_password', 'company_address', 'manager_name', 'manager_phone', 'manager_depart', 'manager_grade', 'other', 'approval', 'nickname', 'admin_name', 'admin_phone', 'code', 'updated_time', 'access_time', 'try_count', 'lock_time']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE {USER_TABLE} SET {",".join(update_list)} WHERE user_id = %s'
        data_list.append(data['user_id'])
        execute_query(query, tuple(data_list))

def delete_user(str_ids):
    query = f'DELETE FROM {USER_TABLE} WHERE user_id in ({str_ids})'

    execute_query(query, ())

def user_detail_by_id(id):
    query = f'SELECT A.*, B.company_name FROM {USER_TABLE} as A LEFT JOIN {COMPANY_TABLE} as B ON A.register_num = B.register_num ' \
            f'WHERE user_id = "{id}"'
    
    res = execute_query(query, ())
    return res[0] if res else None

def user_check_id(id):
    query = f'SELECT * FROM {USER_TABLE} ' \
            f'WHERE nickname = "{id}"'
    
    print(query)
    
    res = execute_query(query, ())
    return res[0] if res else None

def get_user_list():
    query = f'SELECT * FROM {USER_TABLE} WHERE user_type < 3'

    data = execute_query(query, ())
    return data

def get_consignor_list():
    query = f'SELECT A.user_id, A.nickname FROM {USER_TABLE} as A WHERE A.user_type = 2 AND A.approval = 2'

    data = execute_query(query, ())
    return data

def get_project_detail(data):
    where = 'AND 1 '
    if 'admin_id' in data:
        where += f' AND checker_id={data["admin_id"]}'
    if 'company_id' in data:
        where += f' AND company_id={data["company_id"]}'

    query = f'SELECT id, create_date, self_check_date, imp_check_date, delay FROM {PROJECT_DETAIL_TABLE} '\
            f'WHERE project_id={data["project_id"]} {where}'

    print(query)
    data = execute_query(query, ())
    return data

def get_consignee_list():
    query = f'SELECT A.user_id, A.nickname FROM {USER_TABLE} as A WHERE A.user_type = 1 AND A.approval = 2'

    data = execute_query(query, ())
    return data

def get_consignee_list_by_admin(data):
    where = '1 '
    if 'project_id' in data:
        where += f' AND project_id = {data["project_id"]} '
    if 'admin_id' in data:
        where += f' AND checker_id = {data["admin_id"]} '

    query = f'SELECT B.id as company_id, B.company_name, B.company_address, B.manager_name, B.manager_phone from'\
            f'(SELECT company_id FROM {PROJECT_DETAIL_TABLE} WHERE {where}) as A '\
            f'LEFT JOIN (SELECT C.id, C.company_name, D.company_address, D.manager_name, D.manager_phone FROM {COMPANY_TABLE} as C LEFT JOIN (SELECT * FROM {USER_TABLE} WHERE user_type = 1) as D ON C.register_num = D.register_num) as B ON A.company_id = B.id'

    data = execute_query(query, ())
    return data

def get_admin_list():
    query = f'SELECT A.user_id, A.admin_name FROM {USER_TABLE} as A WHERE A.user_type = 0 AND A.approval = 2'

    data = execute_query(query, ())
    return data

def get_approval_user_list():
    query = f'SELECT * FROM {USER_TABLE} WHERE approval < 2 AND user_type > 0'

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
    return execute_query(query, (register_num, company_name))

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
    company_id = data['company_id']
    checklist_id = data['checklist_id']
    privacy_type = data['privacy_type']

    days =  []
    days.append(datetime.now().strftime('%Y-%m-%d'))
    days.append((datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    days.append((datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'))
    days.append((datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'))
    days.append((datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d'))
    days.append((datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'))
    query = f'INSERT INTO {PROJECT_TABLE} (year, name, company_id, checklist_id, privacy_type, created_date, create_from, create_to, self_check_from, self_check_to, imp_check_from, imp_check_to) '\
            f'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    return execute_query(query, (year, name, company_id, checklist_id, privacy_type, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), days[0], days[1], days[2], days[3], days[4], days[5]))

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

def get_project_list(data):
    where = "1 "

    if 'year' in data and data['year'] != 0:
        where += f'AND A.year = {data["year"]} '
    if 'project_name' in data and data['project_name'] != '!@#':
        where += f'AND A.name LIKE "%{data["project_name"]}%" '
    if 'company_name' in data:
        where += f'AND B.company_name LIKE "%{data["company_name"]}%" '
    
    query = f'SELECT A.id, A.year, A.name, B.company_name, C.checklist_item, D.personal_category '\
        f'FROM {PROJECT_TABLE} as A '\
        f'LEFT JOIN {COMPANY_TABLE} as B ON A.company_id = B.id '\
        f'LEFT JOIN {CHECKLIST_TABLE} as C ON A.checklist_id = C.id '\
        f'LEFT JOIN {PERSONAL_CATEGORY_TABLE} as D ON A.privacy_type = D.id '\
        f'WHERE {where}'

    data = execute_query(query, ())
    return data

def get_projects_by_admin(data):
    query = f'SELECT B.* FROM (SELECT project_id '\
        f'FROM {PROJECT_DETAIL_TABLE} '\
        f'WHERE checker_id={data["admin_id"]} '\
        f'GROUP BY project_id) as A '\
        f'LEFT JOIN {PROJECT_TABLE} as B ON A.project_id = B.id '\

    data = execute_query(query, ())
    return data

def get_company_by_user(id):
    query = f'SELECT B.id FROM {USER_TABLE} as A '\
            f'LEFT JOIN {COMPANY_TABLE} as B ON A.register_num = B.register_num '\
            f'WHERE A.user_id = {id} '\

    data = execute_query(query, ())
    return data[0] if data else None

def get_projects_by_consignee(data):
    query = f'SELECT B.* FROM (SELECT project_id '\
        f'FROM {PROJECT_DETAIL_TABLE} '\
        f'WHERE company_id={data["company_id"]} '\
        f'GROUP BY project_id) as A '\
        f'LEFT JOIN {PROJECT_TABLE} as B ON A.project_id = B.id '\

    data = execute_query(query, ())
    return data

def get_projects_by_consignor(data):
    query = f'SELECT * FROM {PROJECT_TABLE} '\
        f'WHERE company_id = {data["company_id"]}'\

    data = execute_query(query, ())
    return data

def get_year_list():
    query = f'SELECT year FROM {PROJECT_TABLE} GROUP BY year ORDER BY year DESC'

    data = execute_query(query, ())
    return data

def get_project_name_list():
    query = f'SELECT name FROM {PROJECT_TABLE} GROUP BY name'

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
    return execute_query(query, (project_id, title, content, create_by, create_time, views, attachment))
    
def get_notice_attachment(id):
    query = f'SELECT create_time, attachment FROM {NOTICE_TABLE} ' \
            f'WHERE id = %s'
    
    res = execute_query(query, (id))
    return res[0] if res else None

def notice_detail_by_id(id):
    query = f'SELECT A.id, B.name, A.title, A.content, A.create_by, A.create_time, A.views, A.attachment, A.project_id FROM {NOTICE_TABLE} as A LEFT JOIN project as B ON A.project_id=B.id WHERE A.id={id}'

    res = execute_query(query, ())
    return res[0] if res else None

def update_notice(data):
    data_list = []
    update_list = []

    for k, v in data.items():
        if k in ['project_id', 'title', 'content', 'attachment']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE {NOTICE_TABLE} SET {",".join(update_list)} WHERE id = %s'
        data_list.append(data['notice_id'])
        execute_query(query, tuple(data_list))

def get_notice_list(search_data):
    where = '1 '

    if 'search_type' in search_data and 'keyword' in search_data and search_data['keyword'] != '':
        if search_data["search_type"] == 1:
            where += f'AND A.title LIKE "%{search_data["keyword"]}%"'
        elif search_data["search_type"] == 2:
            where += f'AND (A.title LIKE "%{search_data["keyword"]}%" OR A.content LIKE "%{search_data["keyword"]}%")'
        elif search_data["search_type"] == 3:
            where += f'AND (A.create_by LIKE "%{search_data["keyword"]}%")'

    query = f'SELECT A.id, B.name, A.title, A.create_by, A.create_time, A.views, A.attachment, A.project_id FROM {NOTICE_TABLE} as A LEFT JOIN project as B ON A.project_id=B.id WHERE {where}'

    data = execute_query(query, ())
    return data

def delete_notice(str_ids):
    query = f'DELETE FROM {NOTICE_TABLE} WHERE id in ({str_ids})'

    execute_query(query, ())

# 문의관련
def register_inquiry(data):
    title = data['title']
    content = data['content']
    password = hashing_password(data['password'])
    author = data['author']
    created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    query = f'INSERT INTO {INQUIRY_TABLE} (title, content, password, author, created_date) '\
            f'VALUES (%s, %s, %s, %s, %s)'
    return execute_query(query, (title, content, password, author, created_date))

def get_inquiry_list():
    query = f'SELECT id, title, content,password, author, created_date FROM {INQUIRY_TABLE}'

    data = execute_query(query, ())
    return data

def delete_inquiry(str_ids):
    query = f'DELETE FROM {INQUIRY_TABLE} WHERE id in ({str_ids})'

    execute_query(query, ())


#개인정보취급분류관리
def register_personal_category(data):
    personal_category = data['personal_category']
    description = data['description']
    
    created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    query = f'INSERT INTO {PERSONAL_CATEGORY_TABLE} (personal_category, description, created_date) '\
            f'VALUES (%s, %s, %s)'
    return execute_query(query, (personal_category, description, created_date))

def get_personal_categories():
    query = f'SELECT id, personal_category, description, created_date FROM {PERSONAL_CATEGORY_TABLE}'

    data = execute_query(query, ())
    return data

def delete_personal_category(str_ids): 
    query = f'DELETE FROM {PERSONAL_CATEGORY_TABLE} WHERE id in ({str_ids})'

    execute_query(query, ())


#개인정보항목관리
def register_personal_info_item(data):
    query = f'DELETE FROM {PERSONAL_INFO_TABLE} WHERE category_id={data["id"]}'
    execute_query(query, ())

    category_id = data['id']
    query = f'INSERT INTO {PERSONAL_INFO_TABLE} (sequence, standard_grade, intermediate_grade, item, merged1, merged2, category_id) VALUES '\

    data_list=[]
    for x in data["data"]:
        sequence = x['sequence']
        standard_grade = x['standard_grade']
        intermediate_grade = x['intermediate_grade']
        item = x['item']
        merged1 = x['merged1']
        merged2 = x['merged2']

        data_list.append(f' ({sequence}, "{standard_grade}", "{intermediate_grade}", "{item}", {merged1}, {merged2}, {category_id})')

    query += ",".join(data_list)
            
    return execute_query(query, ())

def get_personal_info_items_list(category_id):
    query = f'SELECT id, sequence, standard_grade, intermediate_grade, item, merged1, merged2 FROM {PERSONAL_INFO_TABLE} WHERE category_id = %s ORDER BY sequence ASC'
    data = execute_query(query, (category_id,))
    return data


def delete_personal_info_item(id):
    query = f'DELETE FROM {PERSONAL_INFO_TABLE} WHERE id = %s'

    execute_query(query, (id,))




#체크리스트관리
def register_checklist_item(data):
    checklist_item = data['checklist_item']
    description = data['description']
    
    created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    query = f'INSERT INTO {CHECKLIST_TABLE} (checklist_item, description, created_date) '\
            f'VALUES (%s, %s, %s)'
    return execute_query(query, (checklist_item, description, created_date))

def get_checklist_items():
    query = f'SELECT id, checklist_item, description, created_date FROM {CHECKLIST_TABLE}'

    data = execute_query(query, ())
    return data

def get_checklist_item(id):
    query = f'SELECT checklist_item, description, created_date FROM {CHECKLIST_TABLE} WHERE id={id}'

    data = execute_query(query, ())
    return data[0] if data else None

def delete_checklist_item(str_ids):
    query = f'DELETE FROM {CHECKLIST_TABLE} WHERE id in ({str_ids})'

    execute_query(query, ())


def register_project_detail(data):
    project_id = data['project_id']
    company_id = data['company_id']
    work_name = data['work_name']
    checker_id = data['checker_id']
    check_type = data['check_type']

    query = f'INSERT INTO {PROJECT_DETAIL_TABLE} (project_id, company_id, work_name, checker_id, check_type) '\
            f'VALUES (%s, %s, %s, %s, %s)'
    return execute_query(query, (project_id, company_id, work_name, checker_id, check_type))

def register_project_detail_multi(data):
    query = f'INSERT INTO {PROJECT_DETAIL_TABLE} (project_id, company_id, work_name, checker_id, check_type) VALUES '\

    data_list=[]
    for x in data:
        project_id = x['project_id']
        company_id = x['company_id']
        work_name = x['work_name']
        checker_id = x['checker_id']
        check_type = x['check_type']

        data_list.append(f' ({project_id}, {company_id}, "{work_name}", {checker_id}, {check_type})')

    query += ",".join(data_list)
            
    return execute_query(query, ())

def get_project_detail_list(data):
    query = f'SELECT A.id, A.company_id, B.company_name, A.work_name, A.checker_id, C.admin_name, A.check_type '\
        f'FROM {PROJECT_DETAIL_TABLE} as A '\
        f'LEFT JOIN {COMPANY_TABLE} as B ON B.id = A.company_id '\
        f'LEFT JOIN {USER_TABLE} as C ON C.user_id = A.checker_id '\
        f'WHERE project_id = {data["project_id"]}'

    data = execute_query(query, ())
    return data

def delete_project_detail(str_ids):
    query = f'DELETE FROM {PROJECT_DETAIL_TABLE} WHERE id in ({str_ids})'

    execute_query(query, ())

def update_project_detail(data):
    data_list = []
    update_list = []

    for k, v in data.items():
        if k in ['company_id', 'work_name', 'check_type', 'checker_id', 'delay', 'create_date', 'self_check_date', 'imp_check_date', 'check_schedule']:
            update_list.append(f'{k} = %s')
            data_list.append(str(v))

    if update_list.__len__ != 0:
        query = f'UPDATE {PROJECT_DETAIL_TABLE} SET {",".join(update_list)} WHERE id = %s'
        data_list.append(data['id'])
        execute_query(query, tuple(data_list))

def get_project_check_schedule(data):
    where = ''
    if 'admin_id' in data:
        where = f' AND A.checker_id={data["admin_id"]}'
    if 'consignee_id' in data:
        result = get_company_by_user(data['consignee_id'])

        if result == None:
            return FAIL_RESPONSE
        
        data['company_id'] = result[0]
        where = f' AND A.company_id={data["company_id"]}'
    
    query = f'SELECT A.check_schedule, A.id, A.company_id, A.checker_id, A.project_id, D.company_name, E.admin_name '\
        f'FROM {PROJECT_DETAIL_TABLE} as A LEFT JOIN '\
        f'(SELECT C.id as company_id, C.company_name FROM {USER_TABLE} as B LEFT JOIN {COMPANY_TABLE} as C ON B.register_num = C.register_num WHERE B.user_type = 1) as D ON A.company_id = D.company_id '\
        f'LEFT JOIN {USER_TABLE} as E ON A.checker_id = E.user_id '\
        f' WHERE project_id={data["project_id"]} {where}'

    data = execute_query(query, ())
    return data

def register_checklist_info_item(data):
    query = f'DELETE FROM {CHECKLIST_INFO_TABLE} WHERE category_id={data["id"]}'
    execute_query(query, ())

    category_id = data['id']
    query = f'INSERT INTO {CHECKLIST_INFO_TABLE} (sequence, area, domain, item, detail_item, description, attachment, merged1, merged2, category_id) VALUES '\

    data_list=[]
    for x in data["data"]:
        data_list.append(f' ({x["sequence"]}, "{x["area"]}", "{x["domain"]}", "{x["item"]}", "{x["detail_item"]}", "{x["description"]}", "{x["attachment"]}", {x["merged1"]}, {x["merged2"]}, {category_id})')

    query += ",".join(data_list)
            
    return execute_query(query, ())

def get_checklist_info_items_list(category_id):
    query = f'SELECT id, sequence, area, domain, item, detail_item, description, attachment, merged1, merged2 FROM {CHECKLIST_INFO_TABLE} WHERE category_id = %s ORDER BY sequence ASC'
    data = execute_query(query, (category_id,))
    return data

def get_checklist_attachment(id):
    query = f'SELECT B.created_date, A.attachment FROM {CHECKLIST_INFO_TABLE} as A LEFT JOIN {CHECKLIST_TABLE} as B ON A.category_id = B.id' \
            f'WHERE A.id = %s'
    
    res = execute_query(query, (id))
    return res[0] if res else None