import copy
import logging
import random
import string
import uuid
import requests
from datetime import datetime
from pytz import timezone
from werkzeug.exceptions import BadRequest

from flask import request, g
from flask_restx import Resource
from pymysql.err import Error
from twilio.rest import TwilioException

from flaskapp import app
from flaskapp import utils
from flaskapp import db_utils
from flaskapp.flask_namespaces import *
from flaskapp.constants import *

@UserNs.route('/Login')
class Login(Resource):
    def post(self):
        """로그인"""
        login_data: dict = request.json
        print(login_data)
        result = db_utils.check_login(login_data['email'], login_data['password'])

        res={}
        if (result == None):
            res['loginResult'] = 2
        else:
            res['loginResult'] = 1
            res['userData'] = {}
            res['userData']['userEmail'] = result[0]
            res['userData']['userType'] = result[1]
            
        return res
