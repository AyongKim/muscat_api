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
        cursor.execute(query)

        # select 일때만 값 return
        if return_flag:
            query_result = cursor.fetchall()
        else:
            database.commit()

        return query_result

def check_login(email, password):
    password = hashing_password(password)

    print(email)
    print(password)
    query = f'SELECT user_email, user_type FROM user ' \
            f'WHERE user_email = %s AND user_password = %s '
    
    res = execute_query(query, (email, password))
    return res[0] if res else None