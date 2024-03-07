import copy
import logging
from uuid import uuid4
from typing import List
from queue import Queue
from datetime import datetime, timedelta
from pytz import timezone

from elasticsearch import NotFoundError

from flaskapp import es_utils
from flaskapp.constants import *
from flaskapp.enums import CustomScheduleRequestType


def is_custom_schedule(schedule_id: str):
    # schedule_id 가 CLASS 로 시작하면 기존에 있던 수업
    # CUSTOM 으로 시작하면 유저에 의해 생성된 스케줄
    return schedule_id.startswith(CUSTOM_PREFIX)


def is_user_class(schedule_id):
    # USER-CLASS 로 시작하면서 반복되는 스케줄일 경우
    return schedule_id.startswith(USER_CLASS_PREFIX)


def is_academy_class(schedule_id):
    return schedule_id.startswith(CLASS_PREFIX)


def get_user_schedule_of_month(uid, year_month):
    return es_utils.get_document_by_document_id(index=f'{SCHEDULE_INDEX}-{year_month}', doc_id=uid)


def get_regular_schedule_of_month(uid, year_month) -> dict:
    result = get_user_schedule_of_month(uid=uid, year_month=year_month)
    if result['result'] == SUCCESS_VALUE:
        return dict({'data': result['data'][REGULAR_SCHEDULE]}, **SUCCESS_RESPONSE)
    else:
        return result


def get_custom_schedule_of_month(uid, year_month) -> dict:
    result = get_user_schedule_of_month(uid=uid, year_month=year_month)
    if result['result'] == SUCCESS_VALUE:
        return dict({'data': result['data'][CUSTOM_SCHEDULE]}, **SUCCESS_RESPONSE)
    else:
        return result


def get_class_ids_of_regular_schedule_of_month(uid, year_month) -> dict:
    result = get_regular_schedule_of_month(uid=uid, year_month=year_month)
    if result['result'] == SUCCESS_VALUE:
        return dict({'data': result['data'][CLASS_ID]}, **SUCCESS_RESPONSE)
    else:
        return result


def get_user_class_ids_of_month(uid, year_month) -> dict:
    result = get_regular_schedule_of_month(uid=uid, year_month=year_month)
    if result['result'] == SUCCESS_VALUE:
        if USER_CLASS_ID in result['data']:
            return dict({'data': result['data'][USER_CLASS_ID]}, **SUCCESS_RESPONSE)
        else:
            return dict({'data': []}, **SUCCESS_RESPONSE)
    else:
        return result


# ----- Regular Schedule ------
def add_class_into_schedule(uid, class_id):
    now_date = datetime.now(timezone('Asia/Seoul'))
    now_date = datetime(now_date.year, now_date.month, now_date.day)

    class_result = es_utils.get_class_info(class_id)
    if class_result['result'] == SUCCESS_VALUE:
        class_info = class_result['data']

        start_date = datetime.strptime(class_info['start_date'], DATE_FORMAT)
        end_date = datetime.strptime(class_info['end_date'], DATE_FORMAT)
        if class_info['closed'] or end_date <= now_date:
            # already closed class
            return FAIL_RESPONSE

        max_start_date = max(now_date, start_date)
        schedule_year = max_start_date.year
        schedule_month = max_start_date.month

        end_year = end_date.year
        end_month = end_date.month

        while (schedule_year * 12 + schedule_month) <= (end_year * 12 + end_month):
            insert_class_id_of_month(uid=uid, year=schedule_year, month=schedule_month, class_id=class_id)

            schedule_month += 1
            if schedule_month == 13:
                schedule_month = 1
                schedule_year += 1
        return SUCCESS_RESPONSE
    else:
        return FAIL_RESPONSE


def insert_class_id_of_month(uid, year, month, class_id):
    index = f'{SCHEDULE_INDEX}-{year}.{month}'
    class_result = es_utils.get_class_info(class_id)
    if class_result['result'] == FAIL_VALUE:
        return class_result

    class_id_result = get_class_ids_of_regular_schedule_of_month(uid=uid, year_month=f"{year}.{month}")
    if class_id_result['result'] == SUCCESS_VALUE:
        class_ids: List = class_id_result['data']
        if class_id not in class_ids:
            class_ids.append(class_id)
            content = {REGULAR_SCHEDULE: {CLASS_ID: class_ids}}
            return es_utils.update_document_content(index=index, doc_id=uid, content=content)
        else:
            return dict({'reason': 'already_in_schedule'}, **FAIL_RESPONSE)
    else:
        error = class_id_result['error']
        if type(error) == NotFoundError:
            content = {REGULAR_SCHEDULE: {CLASS_ID: [class_id], USER_CLASS_ID: []},
                       CUSTOM_SCHEDULE: []}
            return es_utils.insert_document(index=index, doc_id=uid, document=content)


def remove_class_from_schedule(uid, class_id):

    class_result = es_utils.get_class_info(class_id)
    if class_result['result'] == SUCCESS_VALUE:
        class_info = class_result['data']

        start_date = datetime.strptime(class_info['start_date'], DATE_FORMAT)
        end_date = datetime.strptime(class_info['end_date'], DATE_FORMAT)

        start_year = start_date.year
        start_month = start_date.month

        end_year = end_date.year
        end_month = end_date.month

        while (start_year * 12 + start_month) <= (end_year * 12 + end_month):
            delete_class_id_of_month(uid=uid, year=start_year, month=start_month, class_id=class_id)

            start_month += 1
            if start_month == 13:
                start_month = 1
                start_year += 1

        return SUCCESS_RESPONSE
    else:
        return FAIL_RESPONSE


def delete_class_id_of_month(uid, year, month, class_id):
    year_month = f'{year}.{month}'
    index = f'{SCHEDULE_INDEX}-{year_month}'

    schedule_result = get_user_schedule_of_month(uid, year_month)
    if schedule_result['result'] == SUCCESS_VALUE:
        schedule_data = schedule_result['data']

        # class_id 삭제
        class_ids: List = schedule_data[REGULAR_SCHEDULE]['class_id']
        if class_id in class_ids:
            class_ids.remove(class_id)

        # custom schedule 중에 class_id 관련된 것들 삭제
        new_custom_schedules = []
        custom_schedules = schedule_data[CUSTOM_SCHEDULE]
        for custom_schedule in custom_schedules:
            if custom_schedule['schedule_id'] == class_id:
                continue

            if 'class_info' in custom_schedule and 'class_id' in custom_schedule['class_info']:
                if custom_schedule['class_info']['class_id'] == class_id:
                    continue

            new_custom_schedules.append(custom_schedule)

        content = {REGULAR_SCHEDULE: {CLASS_ID: class_ids}, CUSTOM_SCHEDULE: new_custom_schedules}
        return es_utils.update_document_content(index=index, doc_id=uid, content=content)
    else:
        return FAIL_RESPONSE


# ----- Custom Schedule -----
def update_custom_schedule_document(uid, year_month, custom_schedules):
    content = {CUSTOM_SCHEDULE: custom_schedules}
    return es_utils.update_document_content(index=f'{SCHEDULE_INDEX}-{year_month}', doc_id=uid, content=content)


def add_custom_schedule(uid, year_month, day, schedule_data):
    schedule_id = f'{CUSTOM_PREFIX}-{str(uuid4())}'
    name = schedule_data['name']
    teacher_info = [{"teacher_id": "teacher", "teacher_name": schedule_data['teacher_name']}]
    academy_info = {"academy_id": "academy", "academy_name": schedule_data['academy_name']}

    custom_schedule = {
        'day': day,
        'request_type': CustomScheduleRequestType.ADD,
        SCHEDULE_ID: schedule_id,
        'description': schedule_data['description'],
        'start': schedule_data['start'],
        'end': schedule_data['end'],
        'over_night': False,
        'class_info': {
            'name': name,
            ACADEMY_INFO: academy_info,
            TEACHER_INFO: teacher_info
        }
    }
    insert_result = insert_custom_schedule_of_month(uid, year_month, custom_schedule)
    if insert_result['result'] == SUCCESS_VALUE:
        return dict(SUCCESS_RESPONSE, **{SCHEDULE_ID: schedule_id, CLASS_ID: schedule_id})
    else:
        return insert_result


def insert_custom_schedule_of_month(uid, year_month, custom_schedule):
    custom_schedule_result = get_custom_schedule_of_month(uid=uid, year_month=year_month)
    if custom_schedule_result['result'] == SUCCESS_VALUE:
        custom_schedules = custom_schedule_result['data']
        custom_schedules.append(custom_schedule)
        return update_custom_schedule_document(uid=uid, year_month=year_month, custom_schedules=custom_schedules)
    else:
        error = custom_schedule_result['error']
        if type(error) == NotFoundError:
            content = {REGULAR_SCHEDULE: {CLASS_ID: [], USER_CLASS_ID: []},
                       CUSTOM_SCHEDULE: [custom_schedule]}
            return es_utils.insert_document(index=f'{SCHEDULE_INDEX}-{year_month}', doc_id=uid, document=content)
        else:
            return custom_schedule_result


def add_schedule_delete(uid, schedule_id, year_month, schedule_data):
    day = schedule_data['day']
    start = schedule_data['start']
    end = schedule_data['end']

    custom_schedule_result = get_custom_schedule_of_month(uid=uid, year_month=year_month)
    if custom_schedule_result['result'] == SUCCESS_VALUE:
        custom_schedules = custom_schedule_result['data']
        new_custom_schedules = []

        if is_custom_schedule(schedule_id):
            for custom_schedule in custom_schedules:
                if custom_schedule['day'] == day and custom_schedule[SCHEDULE_ID] == schedule_id:
                    if custom_schedule['start'] == start and custom_schedule['end'] == end:
                        # custom 하게 추가, 변경된 스케줄이 삭제되는 경우
                        continue

                new_custom_schedules.append(custom_schedule)

        else:
            # 학원 수업 또는 유저에 의해 추가된 (반복)수업 (단, 아직 수정되지 않은 경우)
            # DELETE 를 추가만 해주면 된다
            new_custom_schedules += custom_schedules
            new_custom_schedules.append({
                'day': day,
                'request_type': CustomScheduleRequestType.DELETE,
                SCHEDULE_ID: schedule_id,
                'start': start,
                'end': end,
                'over_night': False
            })

        return update_custom_schedule_document(uid=uid, year_month=year_month, custom_schedules=new_custom_schedules)

    else:
        return custom_schedule_result


def update_schedule(uid, schedule_id, original_time_info, new_time_info, description):
    original_year_month = f'{original_time_info["year"]}.{original_time_info["month"]}'
    new_year_month = f'{new_time_info["year"]}.{new_time_info["month"]}'

    # UPDATE 는 DELETE 와 ADD 로 나눠서 처리
    original_custom_schedule_result = get_custom_schedule_of_month(uid=uid, year_month=original_year_month)
    if original_custom_schedule_result['result'] == SUCCESS_VALUE:
        original_custom_schedules = original_custom_schedule_result['data']

        # class(학원, user) 스케줄 처리
        if is_user_class(schedule_id) or is_academy_class(schedule_id):
            updated_original_custom_schedules = original_custom_schedules
            schedule_of_delete = {
                'day': original_time_info['day'],
                'request_type': CustomScheduleRequestType.DELETE,
                SCHEDULE_ID: schedule_id,
                'start': original_time_info['start'],
                'end': original_time_info['end'],
                'over_night': False
            }

            # DELETE 가 이루어져야 ADD 도 수행. 중복 쿼리 방지
            if schedule_of_delete not in updated_original_custom_schedules:
                updated_original_custom_schedules.append(schedule_of_delete)

                # 새로운 custom schedule 생성
                # new_time_info 기준으로 ADD
                custom_schedule_id = f'{CUSTOM_PREFIX}-{str(uuid4())}'
                new_custom_schedule = {
                    'day': new_time_info['day'],
                    'request_type': CustomScheduleRequestType.ADD,
                    SCHEDULE_ID: custom_schedule_id,
                    'description': description,
                    'start': new_time_info['start'],
                    'end': new_time_info['end'],
                    'over_night': False,
                    'class_info': {
                        CLASS_ID: schedule_id
                    }
                }

                if original_year_month == new_year_month:
                    updated_original_custom_schedules.append(new_custom_schedule)
                else:
                    insert_custom_schedule_of_month(uid=uid, year_month=new_year_month,
                                                    custom_schedule=new_custom_schedule)

                schedule_id_dict = {SCHEDULE_ID: custom_schedule_id}
            else:
                schedule_id_dict = {SCHEDULE_ID: None}

        # custom 단일/변경 스케줄 처리
        else:
            schedule_id_dict = {SCHEDULE_ID: None}
            updated_original_custom_schedules = []
            # original_time_info 기준으로 UPDATE
            for original_custom_schedule in original_custom_schedules:
                if original_custom_schedule['day'] == original_time_info['day'] and \
                        original_custom_schedule[SCHEDULE_ID] == schedule_id:
                    if original_custom_schedule['start'] == original_time_info['start'] and \
                            original_custom_schedule['end'] == original_time_info['end']:

                        # custom 스케줄 변경. 중복 쿼리 방지
                        original_custom_schedule.update({
                            'day': new_time_info['day'],
                            'start': new_time_info['start'],
                            'end': new_time_info['end'],
                            'description': description
                        })
                        schedule_id_dict = {SCHEDULE_ID: schedule_id}

                        if original_year_month != new_year_month:
                            insert_custom_schedule_of_month(uid=uid, year_month=new_year_month,
                                                            custom_schedule=original_custom_schedule)
                            continue
                updated_original_custom_schedules.append(original_custom_schedule)

        update_custom_schedule_document(uid=uid, year_month=original_year_month,
                                        custom_schedules=updated_original_custom_schedules)
        return dict(SUCCESS_RESPONSE, **{'schedule_id_dict': schedule_id_dict})

    else:
        return original_custom_schedule_result


def update_schedule_description(uid, schedule_id, year_month, time_info, description):
    custom_schedule_result = get_custom_schedule_of_month(uid=uid, year_month=year_month)
    if custom_schedule_result['result'] == SUCCESS_VALUE:
        custom_schedules = custom_schedule_result['data']
        new_custom_schedules = []

        update_flag = True
        for custom_schedule in custom_schedules:
            if custom_schedule['day'] == time_info['day'] and custom_schedule[SCHEDULE_ID] == schedule_id:
                if custom_schedule['start'] == time_info['start'] and \
                        custom_schedule['end'] == time_info['end']:
                    if custom_schedule['request_type'] in [CustomScheduleRequestType.ADD,
                                                           CustomScheduleRequestType.UPDATE]:
                        # 매치되는 기존의 custom schedule 이 있으면 합치기
                        custom_schedule['description'] = description
                        update_flag = False

            new_custom_schedules.append(custom_schedule)

        # 매치되는 기존의 custom schedule 이 없는 경우, 추가
        if update_flag:
            new_custom_schedules.append({
                'day': time_info['day'],
                'request_type': CustomScheduleRequestType.UPDATE,
                SCHEDULE_ID: schedule_id,
                'description': description,
                'start': time_info['start'],
                'end': time_info['end'],
                'over_night': False
            })

        return update_custom_schedule_document(uid=uid, year_month=year_month,
                                               custom_schedules=new_custom_schedules)

    else:
        return custom_schedule_result


def add_user_class_into_schedule(uid, user_class_info, user_class_id):
    start_date = datetime.strptime(user_class_info['start_date'], DATE_FORMAT)
    end_date = datetime.strptime(user_class_info['end_date'], DATE_FORMAT)

    start_year = start_date.year
    start_month = start_date.month

    end_year = end_date.year
    end_month = end_date.month

    while (start_year * 12 + start_month) <= (end_year * 12 + end_month):
        insert_user_class_id_of_month(uid=uid, year=start_year, month=start_month, user_class_id=user_class_id)

        start_month += 1
        if start_month == 13:
            start_month = 1
            start_year += 1
    return SUCCESS_RESPONSE


def insert_user_class_id_of_month(uid, year, month, user_class_id):
    index = f'{SCHEDULE_INDEX}-{year}.{month}'

    user_class_id_result = get_user_class_ids_of_month(uid=uid, year_month=f"{year}.{month}")
    if user_class_id_result['result'] == SUCCESS_VALUE:
        user_class_ids: List = user_class_id_result['data']
        if user_class_id not in user_class_ids:
            user_class_ids.append(user_class_id)
            content = {REGULAR_SCHEDULE: {USER_CLASS_ID: user_class_ids}}
            return es_utils.update_document_content(index=index, doc_id=uid, content=content)
        else:
            return dict({'reason': 'already_in_schedule'}, **FAIL_RESPONSE)
    else:
        error = user_class_id_result['error']
        if type(error) == NotFoundError:
            content = {REGULAR_SCHEDULE: {CLASS_ID: [], USER_CLASS_ID: [user_class_id]},
                       CUSTOM_SCHEDULE: []}
            return es_utils.insert_document(index=index, doc_id=uid, document=content)


def delete_user_class(uid, class_id):
    user_class_result = es_utils.get_document_by_document_id(index=USER_CLASS_INDEX, doc_id=class_id)
    if user_class_result['result'] == SUCCESS_VALUE:
        user_class_info = user_class_result['data']
        start_date = datetime.strptime(user_class_info['start_date'], DATE_FORMAT)
        end_date = datetime.strptime(user_class_info['end_date'], DATE_FORMAT)

        start_year = start_date.year
        start_month = start_date.month

        end_year = end_date.year
        end_month = end_date.month

        while (start_year * 12 + start_month) <= (end_year * 12 + end_month):
            delete_result = delete_user_class_id_of_month(uid, start_year, start_month, class_id)
            if delete_result['result'] == FAIL_VALUE:
                return FAIL_RESPONSE

            start_month += 1
            if start_month == 13:
                start_month = 1
                start_year += 1

        return es_utils.delete_document(index=USER_CLASS_INDEX, doc_id=class_id)


def delete_user_class_id_of_month(uid, year, month, user_class_id):
    year_month = f'{year}.{month}'
    index = f'{SCHEDULE_INDEX}-{year_month}'

    schedule_result = get_user_schedule_of_month(uid, year_month)
    if schedule_result['result'] == SUCCESS_VALUE:
        schedule_data = schedule_result['data']

        # class_id 삭제
        user_class_ids: List = schedule_data[REGULAR_SCHEDULE]['user_class_id']
        if user_class_id in user_class_ids:
            user_class_ids.remove(user_class_id)

        # custom schedule 중에 class_id 관련된 것들 삭제
        new_custom_schedules = []
        custom_schedules = schedule_data[CUSTOM_SCHEDULE]
        for custom_schedule in custom_schedules:
            if custom_schedule['schedule_id'] == user_class_id:
                continue

            if 'class_info' in custom_schedule and 'class_id' in custom_schedule['class_info']:
                if custom_schedule['class_info']['class_id'] == user_class_id:
                    continue

            new_custom_schedules.append(custom_schedule)

        content = {REGULAR_SCHEDULE: {USER_CLASS_ID: user_class_ids}, CUSTOM_SCHEDULE: new_custom_schedules}
        return es_utils.update_document_content(index=index, doc_id=uid, content=content)
    else:
        return FAIL_RESPONSE


def get_last_day_of_month(date: datetime) -> int:
    if date.month == 12:
        return 31
    return (date.replace(month=date.month + 1, day=1) - timedelta(days=1)).day


def get_regular_week_schedule(user_class_info):
    schedule_result = {}
    for i in range(7):
        schedule_result[str(i)] = []

    regular_class_ids = user_class_info[CLASS_ID]
    for class_id in regular_class_ids:
        class_result = es_utils.get_document_by_document_id(index=CLASS_INDEX, doc_id=class_id)

        if class_result['result'] == SUCCESS_VALUE:
            class_info = class_result['data']
            if class_info['closed']:
                continue

            for regular_schedule in class_info[REGULAR_SCHEDULE]:
                regular_schedule.update({
                    CLASS_ID: class_id,
                    SCHEDULE_ID: class_id,
                    'name': class_info['name'],
                    'description': class_info['description'],
                    'class_info': {
                        ACADEMY_INFO: class_info[ACADEMY_INFO],
                        TEACHER_INFO: class_info[TEACHER_INFO],
                        'subject_info': class_info['subject_info']
                    },
                    'start_date': class_info['start_date'],
                    'end_date': class_info['end_date']
                })

                schedule_result[regular_schedule['week_day']].append(regular_schedule)

    if USER_CLASS_ID in user_class_info:
        user_class_ids = user_class_info[USER_CLASS_ID]
        for class_id in user_class_ids:
            custom_schedule_result = es_utils.get_document_by_document_id(index=USER_CLASS_INDEX,
                                                                          doc_id=class_id)
            if custom_schedule_result['result'] == SUCCESS_VALUE:
                schedule_info = custom_schedule_result['data']
                for regular_schedule in schedule_info[REGULAR_SCHEDULE]:
                    regular_schedule.update({
                        CLASS_ID: class_id,
                        SCHEDULE_ID: class_id,
                        'name': schedule_info['name'],
                        'description': schedule_info['description'],
                        'class_info': {
                            ACADEMY_INFO: schedule_info[ACADEMY_INFO],
                            TEACHER_INFO: schedule_info[TEACHER_INFO]
                        },
                        'start_date': schedule_info['start_date'],
                        'end_date': schedule_info['end_date']
                    })

                    schedule_result[regular_schedule['week_day']].append(regular_schedule)

    return schedule_result


def get_week_preview_schedule_of_class(class_id):
    schedule_result = []

    class_scheduler = Scheduler(class_id=class_id)
    class_info = class_scheduler.get_class_info(class_id)
    start_date = datetime.strptime(class_info['start_date'], DATE_FORMAT)
    end_date = datetime.strptime(class_info['end_date'], DATE_FORMAT)

    now_date = datetime.now(timezone('Asia/Seoul'))
    now_date = datetime.strptime(f'{now_date.year}-{now_date.month}-{now_date.day}', DATE_FORMAT)
    if end_date < now_date:
        return schedule_result
    else:
        if now_date < start_date:
            target_date = start_date
        else:
            target_date = now_date
    monday_date = target_date - timedelta(target_date.weekday())

    schedule_result = class_scheduler.get_week_schedule(monday_date)
    # start_date 가 목요일이고 수업은 월, 수에 있는 경우
    if len(schedule_result) == 0:
        monday_date += timedelta(7)
        schedule_result = class_scheduler.get_week_schedule(monday_date)

    return schedule_result, monday_date.strftime(DATE_FORMAT)


def get_month_preview_schedule_of_class(class_id):
    schedule_result = []

    class_scheduler = Scheduler(class_id=class_id)
    class_info = class_scheduler.get_class_info(class_id)
    start_date = datetime.strptime(class_info['start_date'], DATE_FORMAT)
    end_date = datetime.strptime(class_info['end_date'], DATE_FORMAT)

    now_date = datetime.now(timezone('Asia/Seoul'))
    now_date = datetime.strptime(f'{now_date.year}-{now_date.month}-{now_date.day}', DATE_FORMAT)
    if end_date < now_date:
        return schedule_result
    else:
        if now_date < start_date:
            target_date = start_date
        else:
            target_date = now_date

    schedule_result = class_scheduler.get_month_schedule(year=target_date.year, month=target_date.month)
    return schedule_result, str(target_date.month), str(target_date.year)


def check_day_schedule_overlap(uid, date: datetime, start, end, schedule_id=None, original_time_info=None):
    scheduler = Scheduler(uid=uid)
    result = scheduler.get_day_schedule(date)
    for schedule in result:
        # 같은 날짜 내에서 시간만 수정하는 경우
        if schedule_id and original_time_info:
            if schedule[SCHEDULE_ID] == schedule_id:
                if schedule['start'] == original_time_info['start'] and schedule['end'] == original_time_info['end']:
                    # 수정 하려는 스케줄일 경우 비교 할필요 없음
                    continue

        overlap_check = check_schedule_overlap(target_start=start, target_end=end,
                                               source_start=schedule['start'], source_end=schedule['end'])
        if not overlap_check:
            return dict({
                'overlap_schedule_info': {
                    SCHEDULE_ID: schedule[SCHEDULE_ID],
                    'name': schedule['name'],
                    'year': str(date.year),
                    'month': str(date.month),
                    'day': str(date.day),
                    'weekday': schedule['week_day'],
                    'start': schedule['start'],
                    'end': schedule['end']
                }
            }, **FAIL_RESPONSE)

    return SUCCESS_RESPONSE


def check_class_overlap(uid, class_id):
    class_result = es_utils.get_class_info(class_id)
    if class_result['result'] == FAIL_VALUE:
        return class_result
    class_info = class_result['data']
    return check_schedule_overlaps(uid, class_info)


def check_user_class_overlap(uid, custom_schedule_info):
    return check_schedule_overlaps(uid, custom_schedule_info)


def check_schedule_overlaps(uid, class_info):
    now_date = datetime.now(timezone('Asia/Seoul'))
    now_date = datetime(now_date.year, now_date.month, now_date.day)

    overlap_result = []

    class_start_date = datetime.strptime(class_info['start_date'], DATE_FORMAT)
    class_end_date = datetime.strptime(class_info['end_date'], DATE_FORMAT)

    max_start_date = max(now_date, class_start_date)
    schedule_year = max_start_date.year
    schedule_month = max_start_date.month

    end_year = class_end_date.year
    end_month = class_end_date.month

    while (schedule_year * 12 + schedule_month) <= (end_year * 12 + end_month):
        overlap_result += check_month_schedule_overlap(uid, schedule_year, schedule_month, class_info)

        schedule_month += 1
        if schedule_month == 13:
            schedule_month = 1
            schedule_year += 1

    return overlap_result


def check_month_schedule_overlap(uid, year, month, class_info):
    overlap_result = []
    class_schedules = class_info[REGULAR_SCHEDULE]

    class_start_date = datetime.strptime(class_info['start_date'], DATE_FORMAT)
    class_end_date = datetime.strptime(class_info['end_date'], DATE_FORMAT)

    scheduler = Scheduler(uid=uid)

    total_month_schedule = scheduler.get_total_month_schedule(year_month=f'{year}.{month}')
    if total_month_schedule:
        # 이미 겹칠일 없는 regular schedule 들은 제외
        regular_week_schedule = total_month_schedule['regular']

        refined_week_schedule = {}
        for i in range(7):
            refined_week_schedule[str(i)] = []

        for class_schedule in class_schedules:
            start = class_schedule['start']
            end = class_schedule['end']
            week_day = class_schedule['week_day']

            for regular_schedule in regular_week_schedule[week_day]:
                regular_schedule_start_date = datetime.strptime(regular_schedule['start_date'], DATE_FORMAT)
                regular_schedule_end_date = datetime.strptime(regular_schedule['end_date'], DATE_FORMAT)

                # 수업 기간이 겹치지 않는 경우
                if class_end_date < regular_schedule_start_date or regular_schedule_end_date < class_start_date:
                    continue

                # regular schedule time 이 겹치지 않는 경우
                overlap_check = check_schedule_overlap(target_start=start,
                                                       target_end=end,
                                                       source_start=regular_schedule['start'],
                                                       source_end=regular_schedule['end'])
                if overlap_check:
                    continue
                refined_week_schedule[week_day].append(regular_schedule)
        total_month_schedule['regular'] = refined_week_schedule
        scheduler.total_month_schedule_dict[f'{year}.{month}'] = total_month_schedule

        # 일일 단위로 overlap 검증
        for class_schedule in class_schedules:
            start = class_schedule['start']
            end = class_schedule['end']
            week_day = class_schedule['week_day']

            for day in get_week_days_of_month(year, month, week_day):
                day_schedules = scheduler.get_day_schedule(
                    datetime.strptime(f'{year}-{month}-{day}', DATE_FORMAT))
                for day_schedule in day_schedules:
                    overlap_check = check_schedule_overlap(target_start=start,
                                                           target_end=end,
                                                           source_start=day_schedule['start'],
                                                           source_end=day_schedule['end'])
                    if not overlap_check:
                        overlap_result.append(day_schedule)

    return overlap_result


def check_schedule_overlap(target_start, target_end, source_start, source_end):
    """스케줄이 겹칠 경우 False, 안 겹치면 True"""
    target_start = datetime.strptime(target_start, H_M_FORMAT)
    target_end = datetime.strptime(target_end, H_M_FORMAT)
    source_start = datetime.strptime(source_start, H_M_FORMAT)
    source_end = datetime.strptime(source_end, H_M_FORMAT)
    return (target_end <= source_start) or (source_end <= target_start)


def get_week_days_of_month(year, month, week_day):
    result = []

    first_date = datetime.strptime(f'{year}-{month}-1', DATE_FORMAT)
    if month == 12:
        next_month_first_date = datetime.strptime(f'{year + 1}-1-1', DATE_FORMAT)
    else:
        next_month_first_date = datetime.strptime(f'{year}-{month + 1}-1', DATE_FORMAT)
    last_date = next_month_first_date - timedelta(days=1)
    last_day = last_date.day

    week_day_of_first_date = first_date.weekday()
    day_delta = (int(week_day) - week_day_of_first_date) % 7
    first_week_day = first_date + timedelta(days=day_delta)

    day = first_week_day.day
    while last_day >= day:
        result.append(day)
        day += 7

    return result


class Scheduler:
    def __init__(self, uid=None, class_id=None):
        if not uid and not class_id:
            raise Exception('One of uid or class_id should be specified')

        self.uid = uid
        self.class_id = class_id
        self.total_month_schedule_dict = {}
        self.class_info_dict = {}

    def get_total_month_schedule(self, year_month):
        if year_month not in self.total_month_schedule_dict:
            if self.uid:
                total_month_schedule_result = get_user_schedule_of_month(uid=self.uid, year_month=year_month)
                if total_month_schedule_result['result'] == SUCCESS_VALUE:
                    total_month_schedule = total_month_schedule_result['data']
                    regular_week_schedule = get_regular_week_schedule(total_month_schedule[REGULAR_SCHEDULE])

                    total_custom_schedules = Queue()
                    for i in total_month_schedule[CUSTOM_SCHEDULE]:
                        total_custom_schedules.put(i)

                    self.total_month_schedule_dict[year_month] = {'regular': regular_week_schedule,
                                                                  'custom': total_custom_schedules}
                else:
                    self.total_month_schedule_dict[year_month] = None

            else:
                if self.class_id:
                    regular_week_schedule = get_regular_week_schedule([self.class_id])
                    self.total_month_schedule_dict[year_month] = {'regular': regular_week_schedule,
                                                                  'custom': Queue()}

        return self.total_month_schedule_dict[year_month]

    def get_class_info(self, class_id):
        if class_id not in self.class_info_dict:
            class_result = es_utils.get_class_info(class_id)
            if class_result['result'] == SUCCESS_VALUE:
                self.class_info_dict[class_id] = class_result['data']
            else:
                self.class_info_dict[class_id] = None

        return self.class_info_dict[class_id]

    def get_user_class_info(self, class_id):
        if class_id not in self.class_info_dict:
            class_result = es_utils.get_user_class_info(class_id)
            if class_result['result'] == SUCCESS_VALUE:
                self.class_info_dict[class_id] = class_result['data']
            else:
                self.class_info_dict[class_id] = None

        return self.class_info_dict[class_id]

    def get_day_schedule(self, date: datetime):
        schedule_result = []
        date_info = {'year': date.year,
                     'month': date.month,
                     'day': date.day}
        total_month_schedule = self.get_total_month_schedule(year_month=f'{date.year}.{date.month}')

        if total_month_schedule:
            # custom schedule 중 요청 날짜에 해당하는 일정 수집
            custom_day_schedules = []
            custom_month_schedule: Queue = total_month_schedule['custom']
            for _ in range(len(custom_month_schedule.queue)):
                custom_schedule = custom_month_schedule.get()
                if custom_schedule['day'] == str(date_info['day']):
                    custom_day_schedules.append(custom_schedule)
                    continue
                custom_month_schedule.put(custom_schedule)

            regular_week_schedule = copy.deepcopy(total_month_schedule['regular'])

            # regular schedule 전체와 DELETE custom schedule 전체를 비교하기 위한 queue
            regular_day_schedules = Queue()
            for regular_day_schedule in regular_week_schedule[str(date.weekday())]:
                class_start_date = datetime.strptime(regular_day_schedule.pop('start_date'), DATE_FORMAT)
                class_end_date = datetime.strptime(regular_day_schedule.pop('end_date'), DATE_FORMAT)

                if class_start_date <= date <= class_end_date:
                    regular_day_schedules.put(regular_day_schedule)

            # custom schedule 랜더링
            for custom_schedule in custom_day_schedules:
                custom_schedule.pop('day')
                request_type = custom_schedule.pop('request_type')
                custom_schedule_schedule_id = custom_schedule[SCHEDULE_ID]

                if request_type == CustomScheduleRequestType.ADD:
                    # custom_schedule schedule_id 는 무조건 CUSTOM-*
                    if is_custom_schedule(custom_schedule_schedule_id):
                        if 'class_info' in custom_schedule:
                            base_custom_schedule = {
                                'week_day': str(date.weekday()),
                                'start': custom_schedule['start'],
                                'end': custom_schedule['end'],
                                'over_night': custom_schedule['over_night'],
                                CLASS_ID: None,
                                SCHEDULE_ID: custom_schedule[SCHEDULE_ID],
                                'name': None,
                                'description': custom_schedule['description'],
                                'class_info': None,
                                'date': date_info
                            }

                            # 학원 class 또는 user class 에 대한 변경은 class_id 존재
                            if CLASS_ID in custom_schedule['class_info']:
                                class_id = custom_schedule['class_info'][CLASS_ID]
                                if is_user_class(class_id):
                                    class_info = self.get_user_class_info(class_id)
                                else:
                                    class_info = self.get_class_info(class_id)

                                if not class_info:
                                    continue

                                rendered_schedule = dict(base_custom_schedule, **{
                                    CLASS_ID: class_id,
                                    'name': class_info['name'],
                                    'class_info': {
                                        ACADEMY_INFO: class_info[ACADEMY_INFO],
                                        TEACHER_INFO: class_info[TEACHER_INFO]
                                    }
                                })

                                if is_academy_class(class_id):
                                    rendered_schedule['class_info']['subject_info'] = class_info['subject_info']

                            # class_id 가 없는 것은 class 와 연관이 없는, 유저가 직접 만든 단일 custom 스케줄
                            else:
                                rendered_schedule = dict(base_custom_schedule, **{
                                    CLASS_ID: custom_schedule_schedule_id,
                                    'name': custom_schedule['class_info']['name'],
                                    'class_info': custom_schedule['class_info']
                                })

                            schedule_result.append(rendered_schedule)
                            continue

                        else:
                            logging.warning(f'ADD should have "class_info" but {custom_schedule_schedule_id} does not')
                            continue

                    else:
                        logging.warning(f'ADD request of {custom_schedule_schedule_id} should have '
                                        f'{CUSTOM_PREFIX} prefix')
                        continue

                elif request_type == CustomScheduleRequestType.UPDATE:
                    # custom_schedule_schedule_id 는 무조건 CLASS-* 또는 USER-CLASS-*
                    if is_custom_schedule(custom_schedule_schedule_id):
                        logging.warning(f'UPDATE of custom schedule should not be here : {custom_schedule_schedule_id}')
                        continue
                    else:
                        for j in range(regular_day_schedules.qsize()):
                            regular_day_schedule = regular_day_schedules.get()

                            if custom_schedule_schedule_id == regular_day_schedule[SCHEDULE_ID]:
                                if custom_schedule['start'] == regular_day_schedule['start'] and \
                                        custom_schedule['end'] == regular_day_schedule['end']:
                                    # description update
                                    regular_day_schedule['description'] = custom_schedule['description']

                            regular_day_schedules.put(regular_day_schedule)

                elif request_type == CustomScheduleRequestType.DELETE:
                    # custom_schedule_schedule_id 는 CLASS-* 또는 USER-CLASS
                    for j in range(regular_day_schedules.qsize()):
                        day_schedule = regular_day_schedules.get()

                        if custom_schedule_schedule_id == day_schedule[SCHEDULE_ID]:
                            if custom_schedule['start'] == day_schedule['start'] and \
                                    custom_schedule['end'] == day_schedule['end']:
                                # 날짜, 시작 시간, 종료 시간, class_id 까지 같으면 해당 schedule 은 삭제
                                continue

                        regular_day_schedules.put(day_schedule)

            while regular_day_schedules.qsize() > 0:
                schedule = regular_day_schedules.get()
                schedule['date'] = date_info

                schedule_result.append(schedule)

        return schedule_result

    def get_week_schedule(self, monday_date: datetime):
        schedule_result = []
        for i in range(7):
            date = monday_date + timedelta(days=i)
            schedule_result += self.get_day_schedule(date)

        return schedule_result

    def get_month_schedule(self, year, month):
        schedule_result = []

        first_date_of_target_month = datetime.strptime(f'{year}-{month}-1', DATE_FORMAT)
        week_day_of_first_week = first_date_of_target_month.weekday()
        monday_date = first_date_of_target_month - timedelta(days=week_day_of_first_week)

        while True:
            schedule_result += self.get_week_schedule(monday_date)
            monday_date += timedelta(days=7)
            if monday_date.month != int(month):
                break

        return schedule_result
