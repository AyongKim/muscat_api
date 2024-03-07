import logging
from uuid import uuid4
from datetime import datetime, timedelta
from pytz import timezone

from elasticsearch import Elasticsearch

from flaskapp.constants import *

es_cluster = Elasticsearch(hosts=ES_ENDPOINT)

DEFAULT_START_DATE = '2022-11-01'
DEFAULT_END_DATE = '2100-01-01'


def insert_document(index, doc_id, document: dict):
    res = es_cluster.index(index=index, id=doc_id, document=document)
    status_code = res.meta.status
    if status_code // 100 != 2:
        logging.info(f'Inserting doc failed\nindex: {index}\ndoc_id: {doc_id}\ndocument: {document}')
        raise Exception()

    return SUCCESS_RESPONSE


def update_document_content(index, doc_id, content=None, script=None):
    args = {}
    if content:
        args['doc'] = content
    elif script:
        args['script'] = script

    res = es_cluster.update(index=index, id=doc_id, **args)
    status_code = res.meta.status
    if status_code // 100 != 2:
        logging.error(f'Updating doc failed\nindex: {index}\ndoc_id: {doc_id}\ndocument: {content}')
        raise Exception()

    return SUCCESS_RESPONSE


def delete_document(index, doc_id):
    res = es_cluster.delete(index=index, id=doc_id)
    status_code = res.meta.status
    if status_code // 100 != 2:
        logging.error(f'Updating doc failed\nindex: {index}\ndoc_id: {doc_id}')
        raise Exception()

    return SUCCESS_RESPONSE


def search_documents(index, query, size=100, sort=None, search_after=None):
    result = {}
    try:
        args = {'size': size}

        if sort:
            args['sort'] = sort
            if search_after:
                args['search_after'] = search_after

            result['sort'] = []

        res = es_cluster.search(index=index, query=query, **args)
    except Exception as e:
        return dict({'error': e}, **FAIL_RESPONSE)

    status_code = res.meta.status
    if status_code // 100 != 2:
        logging.info(f'Searching doc failed\nindex: {index}\nquery: {query}')
        raise Exception()

    search_result = res.body['hits']['hits']
    data = [dict({'_id': el['_id']}, **el['_source']) for el in search_result]
    result['data'] = data

    if len(search_result) > 0:
        last_data = search_result[-1]
        # 정렬했을 경우, 마지막 데이터의 sort 값을 다음 검색때 search_after 에 넣어줘야함
        if 'sort' in last_data:
            result['sort'] = last_data['sort']

    return dict(result, **SUCCESS_RESPONSE)


def get_document_by_document_id(index, doc_id):
    try:
        res = es_cluster.get(index=index, id=doc_id)
    except Exception as e:
        return dict({'error': e}, **FAIL_RESPONSE)

    status_code = res.meta.status
    if status_code // 100 != 2:
        logging.info(f'Getting doc failed\nindex: {index}\ndocument_id: {doc_id}')
        raise Exception()

    data = res.body['_source']
    data['_id'] = res.body['_id']
    data['_index'] = res.body['_index']
    return dict({'data': data}, **SUCCESS_RESPONSE)


# ----- Academy -----
def insert_academy_info(academy_id, academy_data):
    teacher_info = academy_data[TEACHER_INFO] if TEACHER_INFO in academy_data else []
    tags = {
        'user_added_tags': [],
        'system_added_tags': []
    }
    if 'tags' in academy_data:
        tags.update(academy_data['tags'])

    address_info = {
        'address': None,
        'address_tag': []
    }
    if 'address_info' in academy_data:
        address_info.update(academy_data['address_info'])

    document = {
        NAME: academy_data[NAME],
        'description': academy_data['description'],
        SUBJECT_INFO: academy_data[SUBJECT_INFO],
        'address_info': address_info,
        'tags': tags,
        TEACHER_INFO: teacher_info,
        'class_count': 0,
        PHONE_NUMBER: academy_data[PHONE_NUMBER],
        'account_number': academy_data['account_number'],
        'homepage_url': academy_data['homepage_url']
    }

    return insert_document(index=ACADEMY_INDEX, doc_id=academy_id, document=document)


def search_academy_info_from_conditions(conditions: dict):
    bool_should_list = []
    bool_must_list = []
    subject_info_nested_bool_must_list = []

    search_after = conditions.pop('sort', None)

    for k, v in conditions.items():
        if k == 'name':
            bool_should_list.append({
                'match': {
                    k: v
                }
            })

        elif k in ['address_tag_id']:
            bool_must_list.append({
                "nested": {
                    "path": "address_info.address_tag",
                    "query": {
                        "term": {
                            f"address_info.address_tag.{k}": v
                        }
                    }
                }
            })

        elif k in ['major_subject_id', 'school_course']:
            term_condition = {
                f'{SUBJECT_INFO}.{k}': v
            }
            subject_info_nested_bool_must_list.append({'terms': term_condition})

        elif k in ['tag_id']:
            bool_should_list.append({
                "nested": {
                    "path": "tags.system_added_tags",
                    "query": {
                        "terms": {
                            "tags.system_added_tags.tag_id": v
                        }
                    }
                }
            })

    if subject_info_nested_bool_must_list:
        bool_must_list.append({
            'nested': {
                'path': SUBJECT_INFO,
                'query': {
                    'bool': {
                        'must': subject_info_nested_bool_must_list
                    }
                }
            }
        })

    query = {
        'bool': {
            'should': bool_should_list,
            'must': bool_must_list
        }
    }

    sort = ["_score",
            {"class_count": "desc"},
            "_id"]

    return search_documents(index=ACADEMY_INDEX, query=query, sort=sort, size=20, search_after=search_after)


def upsert_class_count_of_academy(academy_id):
    script = {
        "source": "ctx._source.class_count += params.class_count",
        "lang": "painless",
        "params": {
            "class_count": 1
        }
    }

    return update_document_content(index=ACADEMY_INDEX, doc_id=academy_id, script=script)


# ----- Teacher -----
def insert_teacher_info(teacher_id, teacher_data):
    belonged_academy_info = teacher_data[ACADEMY_INFO] if ACADEMY_INFO in teacher_data else []
    tags = teacher_data['tags'] if 'tags' in teacher_data else {
        'user_added_tags': [],
        'system_added_tags': []
    }

    document = {
        NAME: teacher_data[NAME],
        SUBJECT_INFO: teacher_data[SUBJECT_INFO],
        'tags': tags,
        ACADEMY_INFO: belonged_academy_info,
        PHONE_NUMBER: teacher_data[PHONE_NUMBER],
        'account_number': teacher_data['account_number'],
        'introduction': teacher_data['introduction'],
        'description': teacher_data['description']
    }

    return insert_document(index=TEACHER_INDEX, doc_id=teacher_id, document=document)


def search_teacher_info_from_conditions(conditions: dict):
    bool_should_list = []
    subject_info_nested_bool_must_list = []

    for k, v in conditions.items():
        if k == 'name':
            bool_should_list.append({
                'match': {
                    k: v
                }
            })

        elif k in ['major_subject_id', 'school_course']:
            term_condition = {
                f'{SUBJECT_INFO}.{k}': v
            }
            subject_info_nested_bool_must_list.append({'terms': term_condition})

        elif k in ['tag_id']:
            bool_should_list.append({
                "nested": {
                    "path": "tags.system_added_tags",
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "terms": {
                                        "tags.system_added_tags.tag_id": v
                                    }
                                }
                            ]
                        }
                    }
                }
            })

    if subject_info_nested_bool_must_list:
        bool_should_list.append({
            'nested': {
                'path': SUBJECT_INFO,
                'query': {
                    'bool': {
                        'must': subject_info_nested_bool_must_list
                    }
                }
            }
        })

    query = {
        'bool': {
            'should': bool_should_list
        }
    }
    return search_documents(index=TEACHER_INDEX, query=query)


# ----- Class -----
def insert_class_info(class_data: dict, class_id=None):
    teacher_info = class_data[TEACHER_INFO] if TEACHER_INFO in class_data else []

    academy_info = {}
    if ACADEMY_INFO in class_data:
        academy_info = class_data[ACADEMY_INFO]

    if not teacher_info and not academy_info:
        raise Exception('At least one of teacher or academy should be specified')

    tags = class_data['tags'] if 'tags' in class_data else {
        'user_added_tags': [],
        'system_added_tags': []
    }
    closed = class_data['closed'] if 'closed' in class_data else False

    now_date = datetime.now()
    start_date = now_date.strftime(DATE_FORMAT)
    if ('start_date' in class_data) and class_data['start_date']:
        start_date = class_data['start_date']

    end_date = (now_date + timedelta(days=90)).strftime(DATE_FORMAT)
    if ('end_date' in class_data) and class_data['end_date']:
        end_date = class_data['end_date']

    regular_schedules = []
    for regular_schedule in class_data[REGULAR_SCHEDULE]:
        start_time = f"{regular_schedule['start']['hour']}:{regular_schedule['start']['minute']}"
        start_time = datetime.strptime(start_time, H_M_FORMAT).strftime(H_M_FORMAT)

        end_time = f"{regular_schedule['end']['hour']}:{regular_schedule['end']['minute']}"
        end_time = datetime.strptime(end_time, H_M_FORMAT).strftime(H_M_FORMAT)

        over_night = regular_schedule['over_night'] if 'over_night' in regular_schedule else False

        regular_schedules.append({
            'week_day': regular_schedule['week_day'],
            'start': start_time,
            'end': end_time,
            'over_night': over_night
        })

    document = {
        NAME: class_data[NAME],
        'description': class_data['description'],
        SUBJECT_INFO: class_data[SUBJECT_INFO],
        'tags': tags,
        ACADEMY_INFO: academy_info,
        TEACHER_INFO: teacher_info,
        'created_date': now_date.strftime('%Y-%m-%d %H:%M'),
        'start_date': start_date,
        'end_date': end_date,
        'closed': closed,
        REGULAR_SCHEDULE: regular_schedules
    }

    if class_id:
        return update_document_content(index=CLASS_INDEX, doc_id=class_id, content=document)
    else:
        class_id = f'{CLASS_PREFIX}-{str(uuid4())}'
        return dict(insert_document(index=CLASS_INDEX, doc_id=class_id, document=document), **{'class_id': class_id})


def search_class_info_from_conditions(conditions: dict, exclude_overdue: bool = True, exclude_closed: bool = True, batch_size: int = 20):
    bool_must_list = []
    subject_info_nested_bool_must_list = []
    subject_info_nested_bool_should_list = []
    bool_should_list = []

    time_schedule_list = []

    search_after = conditions.pop('sort', None)

    start_time = conditions.pop('start', None)
    if start_time:
        time_schedule_list.append({
            "range": {
                f"{REGULAR_SCHEDULE}.start": {
                    "gte": start_time
                }
            }
        })

    end_time = conditions.pop('end', None)
    if end_time:
        time_schedule_list.append({
            "range": {
                f"{REGULAR_SCHEDULE}.end": {
                    "lte": end_time
                }
            }
        })

    for k, v in conditions.items():
        if k == 'name':
            bool_should_list.append({
                'match': {
                    k: v
                }
            })

        elif k in ['address_tag_id']:
            bool_must_list.append({
                "nested": {
                    "path": f"{ACADEMY_INFO}.address_tag",
                    "query": {
                        "term": {
                            f"{ACADEMY_INFO}.address_tag.{k}": v
                        }
                    }
                }
            })

        elif k == 'academy_id':
            bool_must_list.append({
                'term': {
                    f'{ACADEMY_INFO}.{k}': v
                }
            })

        elif k == 'teacher_id':
            bool_must_list.append({
                'term': {
                    f'{TEACHER_INFO}.{k}': v
                }
            })

        elif k in ['major_subject_id', 'school_course']:
            term_condition = {
                f'{SUBJECT_INFO}.{k}': v
            }
            subject_info_nested_bool_must_list.append({'term': term_condition})

        elif k in ['subject_id']:
            terms_condition = {
                f'{SUBJECT_INFO}.{k}': v
            }
            subject_info_nested_bool_must_list.append({'terms': terms_condition})

        elif k in [GRADE]:
            term_condition = {
                f'{SUBJECT_INFO}.{k}': v
            }
            subject_info_nested_bool_should_list.append({'term': term_condition})

        elif k == 'week_day':
            for weekday in v:
                regular_schedule_condition = [{
                    "term": {
                        f"{REGULAR_SCHEDULE}.{k}": weekday
                    }
                }]
                regular_schedule_condition += time_schedule_list

                bool_should_list.append({
                    "nested": {
                        "path": REGULAR_SCHEDULE,
                        "query": {
                            "bool": {
                                # 월요일 17~20 시 라는 스케줄이 지켜져야함. 화요일 17~20이 나오지 않으려면 must 사용
                                "must": regular_schedule_condition
                            }
                        }
                    }
                })

    if subject_info_nested_bool_must_list:
        bool_must_list.append({
            'nested': {
                'path': SUBJECT_INFO,
                'query': {
                    'bool': {
                        'must': subject_info_nested_bool_must_list
                    }
                }
            }
        })

    if subject_info_nested_bool_should_list:
        bool_should_list.append({
            'nested': {
                'path': SUBJECT_INFO,
                'query': {
                    'bool': {
                        'should': subject_info_nested_bool_should_list
                    }
                }
            }
        })

    bool_query = {
        'must': bool_must_list,
        'should': bool_should_list
    }

    boolean_filter = []
    if exclude_overdue:
        now = datetime.now(timezone('Asia/Seoul'))
        boolean_filter.append({
            'range': {
                'end_date': {
                    'gte': now.strftime('%Y-%m-%d')
                }
            }
        })

    if exclude_closed:
        boolean_filter.append({
            'term': {
                'closed': False
            }
        })

    if len(boolean_filter) > 0:
        bool_query['filter'] = boolean_filter

    query = {
        'bool': bool_query
    }

    sort = ["_score",
            "_id"]

    return search_documents(index=CLASS_INDEX, query=query, sort=sort, search_after=search_after, size=batch_size)


def get_class_info(class_id):
    return get_document_by_document_id(index=CLASS_INDEX, doc_id=class_id)


def get_user_class_info(class_id):
    return get_document_by_document_id(index=USER_CLASS_INDEX, doc_id=class_id)


def insert_user_class_info(user_class_info):
    user_class_info['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    user_class_id = f'{USER_CLASS_PREFIX}-{str(uuid4())}'
    insert_result = insert_document(index=USER_CLASS_INDEX,
                                    doc_id=user_class_id,
                                    document=user_class_info)
    return dict(insert_result, **{USER_CLASS_ID: user_class_id})
