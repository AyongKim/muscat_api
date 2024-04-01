import os
import boto3

DATE_FORMAT = '%Y-%m-%d'
H_M_FORMAT = '%H:%M'
H_M_S_FORMATE = '%H:%M:%S'

# ----- Database -----
DB_USER = 'admin'
DB_PASSWORD = 'adminmuscat'
DB_ENDPOINT = 'muscat.cro2kqu2go52.eu-north-1.rds.amazonaws.com'
DB_PROT = 3306

ALL_CLASS_DB = 'user'

USER_TABLE = 'user'
COMPANY_TABLE = 'company'
PROJECT_TABLE = 'project'
PROJECT_DETAIL_TABLE = 'project_detail'
NOTICE_TABLE = 'notice'
CHECKLIST_TABLE = 'check_list'
CHECKLIST_INFO_TABLE = 'check_list_info'
CHECKLIST_RESULT_TABLE = 'check_list_result'
INQUIRY_TABLE = 'inquiry'
PERSONAL_CATEGORY_TABLE = 'personal_category'
PERSONAL_INFO_TABLE = 'personal_info'
 


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