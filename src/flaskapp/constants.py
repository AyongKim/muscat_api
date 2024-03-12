import os
import boto3

DATE_FORMAT = '%Y-%m-%d'
H_M_FORMAT = '%H:%M'
H_M_S_FORMATE = '%H:%M:%S'

# ----- Database -----
DB_USER = 'admin'
DB_PASSWORD = '1q2w3e4r!'
DB_ENDPOINT = 'all-class-db-dev.ckp8bphimfd6.ap-northeast-2.rds.amazonaws.com'
DB_PROT = 3306

ALL_CLASS_DB = 'user'

USER_TABLE = 'user'
COMPANY_TABLE = 'company'
PROJECT_TABLE = 'project'
NOTICE_TABLE = 'notice'
CHECKLIST_TABLE = 'checklist'

NOT_MATCHED_VALUE = 'NOT_MATCHED'
MATCHED_VALUE = 'MATCHED'
NONE_VALUE = 'NONE'
SELECTED = 1
NOT_SELECTED = 0

# ----- User -----
FAIL_VALUE = 'FAIL'
SUCCESS_VALUE = 'SUCCESS'
FAIL_RESPONSE = {'result': FAIL_VALUE}
SUCCESS_RESPONSE = {'result': SUCCESS_VALUE}