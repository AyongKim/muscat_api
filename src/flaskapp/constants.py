import os
import boto3

DATE_FORMAT = '%Y-%m-%d'
H_M_FORMAT = '%H:%M'
H_M_S_FORMATE = '%H:%M:%S'

# ----- Database -----
DB_USER = 'root'
DB_PASSWORD = ''
DB_ENDPOINT = 'localhost'
DB_PROT = 3306

ALL_CLASS_DB = 'muscat'

USER_TABLE = 'user'
PASSWORD_TABLE = 'password'
STUDENT_TABLE = 'student'
PAIRING_TABLE = 'pairing'
TEMP_STUDENT_TABLE = 'temp_student'
LOGIN_TOKEN_TABLE = 'login_token'
SCHOOL_TABLE = 'school'
SUBJECT_TABLE = 'subject'
VERIFY_PHONE_NUMBER = 'verify_phone_number'
TAG_TABLE = 'tag'
ADDRESS_TAG_TABLE = 'address_tag'
AGREE_TABLE = 'agree'
ACADEMY_NOTICE_TABLE = 'academy_notice'
ACADEMY_CLASS_NOTICE_TABLE = 'academy_class_notice'
ALLCLASS_NOTICE_TABLE = 'allclass_notice'
ADVERTISEMENT_TABLE = 'advertisement'

NOT_MATCHED_VALUE = 'NOT_MATCHED'
MATCHED_VALUE = 'MATCHED'
NONE_VALUE = 'NONE'
SELECTED = 1
NOT_SELECTED = 0
