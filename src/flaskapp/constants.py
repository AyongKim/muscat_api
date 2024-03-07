import os
import boto3

STAGE = os.environ.get('STAGE')
PROD = 'prod'
DEV = 'dev'
if STAGE not in [PROD, DEV]:
    raise Exception(f'STAGE env is not set properly : {STAGE}')


def _get_environment_value_of_stage(param_name):
    ssm = boto3.client('ssm', region_name='ap-northeast-2')
    response = ssm.get_parameters(
        Names=[f'/{STAGE}/{param_name}'],
        WithDecryption=True
    )
    credentials = response['Parameters'][0]['Value']
    return credentials


SCHOOL_OPEN_API_ENDPOINT = 'https://open.neis.go.kr/hub/schoolInfo'
SCHOOL_OPEN_API_KEY = _get_environment_value_of_stage('SCHOOL_OPEN_API_KEY')
SCHOOL_COURSES = ['elementary', 'middle', 'high']

TWILIO_ACCOUNT_SID = _get_environment_value_of_stage('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = _get_environment_value_of_stage('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = _get_environment_value_of_stage('TWILIO_PHONE_NUMBER')

S3_BUCKET = _get_environment_value_of_stage('S3_BUCKET')
CLOUDFRONT_ID = _get_environment_value_of_stage('CLOUDFRONT_ID')
CLOUD_FRONT_URL = _get_environment_value_of_stage('CLOUD_FRONT_URL')

AUTHORIZATION_HEADER = {
    'Authorization': {
        'in': 'header',
        'description': 'Bearer JWT_TOKEN'
    }
}

IGNORE_OVERLAP_FLAG = 'true'
DEFAULT_OVERLAP_FLAG = 'false'

DATE_FORMAT = '%Y-%m-%d'
H_M_FORMAT = '%H:%M'
H_M_S_FORMATE = '%H:%M:%S'

# ----- Database -----
DB_USER = 'admin'
DB_PASSWORD = _get_environment_value_of_stage('DB_PASSWORD')
DB_ENDPOINT = _get_environment_value_of_stage('DB_ENDPOINT')
DB_PROT = 3306

ALL_CLASS_DB = 'all_class_db'

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

# ----- ES -----
ES_ENDPOINT = _get_environment_value_of_stage('ES_ENDPOINT')

ACADEMY_INDEX = 'academy'
TEACHER_INDEX = 'teacher'
CLASS_INDEX = 'class'
SCHEDULE_INDEX = 'schedule'
USER_CLASS_INDEX = 'user-class'

# ----- JWT -----
JWT_SECRET_KEY = _get_environment_value_of_stage('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_TOKEN_EXPIRE_TIME_IN_MINUTE = 60 * 24 * 10

# ----- User -----
FAIL_VALUE = 'FAIL'
SUCCESS_VALUE = 'SUCCESS'
FAIL_RESPONSE = {'result': FAIL_VALUE}
SUCCESS_RESPONSE = {'result': SUCCESS_VALUE}

EMAIL = 'email'
PASSWORD = 'password'
NICKNAME = 'nickname'
USER_TYPE = 'user_type'
NAME = 'name'
BIRTHDAY = 'birthday'
GENDER = 'gender'
PHONE_NUMBER = 'phone_number'
GRADE = 'grade'
PROVIDER = 'provider'
PROVIDER_ID = 'provider_id'

# ----- Class -----
SUBJECT_INFO = 'subject_info'
ACADEMY_INFO = 'academy_info'
TEACHER_INFO = 'teacher_info'
REGULAR_SCHEDULE = 'regular_schedule'
CUSTOM_SCHEDULE = 'custom_schedule'

CLASS_ID = 'class_id'
USER_CLASS_ID = 'user_class_id'
SCHEDULE_ID = 'schedule_id'

CLASS_PREFIX = 'CLASS'
USER_CLASS_PREFIX = 'USER-CLASS'
CUSTOM_PREFIX = 'CUSTOM'

SUBJECT_INFO_ESSENTIAL_KEYS = ['major_subject_name', 'major_subject_id', 'school_course', 'subject_name', 'subject_id']
