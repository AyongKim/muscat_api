from flask_restx import fields

success_field = fields.String(example='success')
fail_field = fields.String(example='fail')
error_reason_field = fields.String(example='Error Reason')
error_message_field = fields.String(example='something_is_bad')

img_url_field = fields.String(description='base64 encoding 된 url', example='Sd9dj29rh393j82eh2eh7')

uid_field = fields.String(description='uid', example='asdga-asds-abva-asdf', required=True)
student_uid_field = fields.String(description='자녀의 uid', example='asdga-asdfas-abva-asdf')

user_type_field = fields.String(description='user type\n1: Student\n2: Parent\n3: Teacher\n4: Academy',
                                example='1',
                                required=True)
student_user_type_field = fields.String(description='1: Student', example='1', required=True)
parent_user_type_field = fields.String(description='2: Parent', example='2', required=True)
teacher_user_type_field = fields.String(description='3: Teacher', example='3', required=True)
academy_user_type_field = fields.String(description='4: Academy', example='4', required=True)

user_name_field = fields.String(description='User 이름', example='김올클')
teacher_name_field = fields.String(description='Teacher 이름', example='김올클')
academy_name_field = fields.String(description='Academy 이름', example='메가스터디')

email_field = fields.String(description='User email', example='allclass@gmail.com', required=True)
password_field = fields.String(description='User password', example='1q2w3e4r', required=True)
nickname_field = fields.String(description='User nickname. Less than 10', example='ricky')
provider_field = fields.String(description='K: 카카오\nN: 네이버\nG: 구글\nA: 애플', example='K, N, G, A', required=True,
                               enum=['K', 'N', 'G', 'A'])
provider_id_field = fields.String(description='login provider 에서 제공하는 provider id', example='12351235136414')
phone_number_field = fields.String(description='User phone number ( - 없이)', example='01012345678')
gender_field = fields.String(description='User gender', example='male/female')
birthday_field = fields.String(description='User birthday', example='1995-01-01')
grade_field = fields.Integer(description='1~6 : 초등\n7~9 : 중등\n10~12 : 고등', exampl=6)
grade_field_str = fields.String(description='1~6 : 초등\n7~9 : 중등\n10~12 : 고등', example='9')
profile_numbering_field = fields.Integer(description='profile 사진의 넘버링')

get_academy_info_flag = fields.String(description='학원 정보 수신 동의, 0은 비동의, 1은 동의', example='1')
provide_personal_info_flag = fields.String(description='학원 정보 수신 동의, 0은 비동의, 1은 동의', example='1')

is_paired_field = fields.Boolean(description='paired 가 됐는지 여부', example=False)
selected_field = fields.Boolean(description='현재 select 된 학생인지 여부', example=True)

token_field = fields.String(example='A1B2C3DE')
code_field = fields.String(example='482741')
jwt_token_field = fields.String(description='login token. It should be in header with "Authorization" key',
                                example='eJasdlkfhasd.asdfasdf.asdfasdf')

account_number_field = fields.String(description='academy 계좌 번호 (- 없이. 선택 사항)', exampl='1298213401838')
homepage_url_field = fields.String(description='academy homepage url', exampl='home.com')
address_field = fields.String(description='주소 정보', example='서울특별시 양천구 신목로5길 11-6')

major_subject_name_field = fields.String(description='Major Subject name', exampl='수학')
major_subject_id_field = fields.String(description='Major Subject ID. Refer to DB', example='4')
subject_name_field = fields.String(description='Subject name', exampl='KMO')
subject_id_field = fields.String(description='Subject ID. Refer to DB', example='100')

introduction_field = fields.String(description='선생님 홍보 한줄 문구', example='대치동 수학 1타 강사의 전설')
teacher_description_field = fields.String(description='선생님의 디테일한 설명', example='전) 대치 미탐 수학강사.. 등')

tag_id_field = fields.String(description='Tag ID', example='1')
tag_name_filed = fields.String(description='Tag name', example='수학전문')
address_tag_name_filed = fields.String(description='Tag name', example='대치')

school_course_field = fields.String(enum=['초등학생', '중학생', '고등학생'])
school_code_field = fields.String(description='학생의 School code', example='708093')
school_name_field = fields.String(description='학교 이름', example='서울신목초등학교')
school_name_search_field = fields.String(description='학교 이름으로 검색. 최소 2글자 이상 검색', example='신목')

class_id_field = fields.String(description='class_id', example='CLASS-asdga-asds-abva')
class_name_field = fields.String(description='Class 이름', example='고1 수학 선행반')
class_description_field = fields.String(description='수업 설명', example='미적분 심화 수업')
class_count_field = fields.Integer(description='학원에 속한 class 개수', example=1)
user_class_id_field = fields.String(description='유저가 만든 수업의 class_id', example='USER-CLASS-asdga-asds')

schedule_id_field = fields.String(description='schedule id. 기존 schedule 이면 CLASS-*, 유저가 추가했으면 CUSTOM-*',
                                  example='CLASS/CUSTOM-asdga-asds-abva')
year_field = fields.String(description='년도 정보', example='2023')
month_field = fields.String(description='월 정보', example='1')
day_field = fields.String(description='일(날짜) 정보', example='29')
date_field = fields.String(description='class start date', example='2022-12-27')
date_field_2 = fields.String(description='date format', example='23.12.27')
time_field = fields.String(description='시간 정보', example='19:00')
weekday_field = fields.String(description='요일 정보', example='4')
over_night_field = fields.Boolean(description='날짜를 넘어가는 지에 대한 flag', example=False)
closed_class_field = fields.Boolean(description='closed boolean', example=False)

original_time_field = fields.String(description='기존 schedule의 start/end 시간 정보', example='19:00')
new_time_field = fields.String(description='새로운 schedule의 start/end 시간 정보', example='21:00')
memo_field = fields.String(description='유저가 쓴 description/memo 정보', example='시험기간 보충 수업')

ignore_overlap_field = fields.String(description='overlap 체크를 무시하고 넣기. true/false', enum=['true', 'false'])
sort_field = fields.String(description='pagenation 에 사용할 sort 정보', example='1,0,628176d4-fec1-4cf6-8499-ec0f1bab0')
schedule_count_field = fields.Integer(description='schedule 블록 개수', example=3)
image_path_field = fields.String(description='Cloud Front url 과 이미지 이름 사이의 이미지 path', example='user/profile')

doc_id_field = fields.Integer(description='db 상 문서의 id. Notice 에서 사용', example=5)
title_field = fields.String(description='글의 제목', example='글의 제목')
content_field = fields.String(description='글의 내용', example='글의 제목')

ad_id_field = fields.Integer(description='db 상 ad의 id', example=5)
image_name_field = fields.String(description='ad 이미지 이름', example='628176d4-fec1-4cf6-8499-ec0f1bab0')
redirect_url_field = fields.String(description='광고를 눌렀을때 redirect 되는 url', example='http://allclass-dev.com:1001/')
ad_location_id_field = fields.String(description='위치에 따른 광고 번호', example='2')
