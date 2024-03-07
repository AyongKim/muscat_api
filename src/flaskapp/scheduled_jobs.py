import time
from datetime import datetime
from pytz import timezone

import requests
from apscheduler.schedulers.background import BackgroundScheduler

from flaskapp.constants import ES_ENDPOINT, STAGE, PROD, DEV, ACADEMY_INDEX, FAIL_RESPONSE, USER_TABLE
from flaskapp.db_utils import _connect_db
from flaskapp.es_utils import search_class_info_from_conditions, update_document_content

background_scheduler = BackgroundScheduler(daemon=True, timezone='Asia/Seoul')


@background_scheduler.scheduled_job('cron', hour='2', minute='0', id='1')
def create_es_snapshot():
    if STAGE == PROD:
        snapshot_repo = 'es-backup-prod'
    elif STAGE == DEV:
        snapshot_repo = 'es-dev-snapshot'
    else:
        raise Exception(f'STAGE env is not set properly : {STAGE}')

    res = requests.get(f'{ES_ENDPOINT}/_cat/snapshots?format=json')
    res.raise_for_status()
    snapshots = res.json()
    if len(snapshots) > 10:
        oldest_snapshot = snapshots[0]['id']
        print(f'Deleting old snapshots : {oldest_snapshot}')
        requests.delete(f'{ES_ENDPOINT}/_snapshot/{snapshot_repo}/{oldest_snapshot}')

    now = datetime.now(timezone('Asia/Seoul'))
    time_format = now.strftime('%Y%m%d')
    new_snapshot_name = f'es-{STAGE}-{time_format}'
    retry_count = 10
    delay = 120
    while retry_count > 0:
        try:
            requests.put(f'{ES_ENDPOINT}/_snapshot/{snapshot_repo}/{new_snapshot_name}')
            print(f'Created ES snapshot : {new_snapshot_name}')
            break
        except Exception as e:
            print(f'Exception happens while creating ES snapshot : {e}')
            print(f'Re-try after {delay} seconds')
            retry_count -= 1
            time.sleep(delay)


@background_scheduler.scheduled_job('cron', day='1', hour='4', minute='0', id='2')
def update_class_count_of_academy():
    delay = 1
    print('Start updating class count of academy info')

    def execute_query(base_query: str, var_tuple: tuple):
        database = _connect_db()
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

    def get_all_academy():
        query = f'SELECT uid FROM {USER_TABLE} WHERE user_type = %s'
        res = execute_query(query, (4,))
        return [el[0] for el in res]

    academy_ids = get_all_academy()

    for academy_id in academy_ids:
        class_of_academy = search_class_info_from_conditions(conditions={'academy_id': academy_id}, batch_size=10000)
        class_count = len(class_of_academy['data'])
        result = update_document_content(index=ACADEMY_INDEX, doc_id=academy_id, content={'class_count': class_count})

        if result['result'] == FAIL_RESPONSE:
            print(f'Fail : {result}')
        else:
            print(f'Success : {academy_id} / {class_count}')
        time.sleep(delay)
    print('Done')
