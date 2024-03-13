from enum import Enum
from typing import List

from flaskapp.constants import FAIL_RESPONSE


class FailResponse:
    INVALID_PASSWORD = dict({'reason': 'invalid_password'}, **FAIL_RESPONSE)
    REGISTERED_USER = dict({'reason': 'registered_user'}, **FAIL_RESPONSE)
    NOT_REGISTERED_USER = dict({'reason': 'not_registered_user'}, **FAIL_RESPONSE)
    NOT_REGISTERED_NOTICE = dict({'reason': 'not_registered_notice'}, **FAIL_RESPONSE)
    INACTIVE_USER = dict({'reason': 'inactive_user'}, **FAIL_RESPONSE)
    UNVERIFIED_PHONE_NUMBER = dict({'reason': 'unverified_phone_number'}, **FAIL_RESPONSE)
    INVALID_TOKEN = dict({'reason': 'invalid_token'}, **FAIL_RESPONSE)
    NOT_PAIRED = dict({'reason': 'not_paired_with_any_student'}, **FAIL_RESPONSE)
    DUPLICATED_NICKNAME = dict({'reason': 'duplicated_nickname'}, **FAIL_RESPONSE)
    INVALID_CODE = dict({'reason': 'invalid_code'}, **FAIL_RESPONSE)
    EXPIRED_CODE = dict({'reason': 'expired_code'}, **FAIL_RESPONSE)
    IMPROPER_SCHEDULE = dict({'reason': 'improper_schedule'}, **FAIL_RESPONSE)

    @classmethod
    def from_exception(cls, exception_source, exception: Exception):
        return dict(
            {
                'reason': f'{exception_source}_exception',
                'exception': {
                    'exception_type': type(exception).__name__,
                    'exception_arg': exception.args,
                },
                'error_message': f'{type(exception).__name__}: {exception.args}'
            }, **FAIL_RESPONSE
        )

    @classmethod
    def missed_value_exception(cls, key, data):
        return dict(
            {
                'reason': 'missed_value',
                'exception': {
                    'original_data': data,
                    'missed_key': key
                },
                'error_message': f'VALUE of "{key}" KEY in {data} is empty'
            }, **FAIL_RESPONSE
        )

    @classmethod
    def missed_key_exception(cls, key, data):
        return dict(
            {
                'reason': 'missed_key',
                'exception': {
                    'original_data': data,
                    'missed_key': key
                },
                'error_message': f'{data} does not contain "{key}" KEY'
            }, **FAIL_RESPONSE
        )

    @classmethod
    def improper_user_type_exception(cls, user_type, valid_user_types: List):
        return dict(
            {
                'reason': 'improper_user_type',
                'exception': {
                    'user_type': user_type,
                    'valid_user_types': valid_user_types
                },
                'error_message': f'USER TYPE "{user_type}" is not proper for this request'
            }, **FAIL_RESPONSE
        )

    @classmethod
    def invalid_token_exception(cls, error_message):
        fail_response = FailResponse()
        return dict(
            {'error_message': error_message}, **fail_response.INVALID_TOKEN
        )

    @classmethod
    def overlap_schedule(cls, overlap_schedule_info):
        return dict(
            {
                'reason': 'overlap_schedule',
                'exception': {'overlap_schedule_info': overlap_schedule_info},
                'error_message': f'Edited schedule is overlapped with other schedule'
            }, **FAIL_RESPONSE
        )
