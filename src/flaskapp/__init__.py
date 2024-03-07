from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

from pytz import timezone, UTC
from flask import Flask
from flask_restx import Api
from flask_cors import CORS
from flask_log_request_id import RequestID, RequestIDLogFilter



app = Flask(__name__)

CORS(app, origins=['localhost:3000'])
#CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# file size
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024


# logging
class Formatter(logging.Formatter):
    """override logging.Formatter to use an aware datetime object"""
    def converter(self, timestamp):
        # Create datetime in UTC
        dt = datetime.fromtimestamp(timestamp, tz=UTC)
        # Change datetime's timezone
        return dt.astimezone(timezone('Asia/Seoul'))

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            try:
                s = dt.isoformat(timespec='milliseconds')
            except TypeError:
                s = dt.isoformat()
        return s


now = datetime.now(timezone('Asia/Seoul'))
time_format = now.strftime('%Y%m%d-%H%M')

app.config['LOGGING_LEVEL'] = logging.INFO
app.config['LOGGING_FORMAT'] = '[%(asctime)s  %(filename)s:%(lineno)d  %(levelname)s %(request_id)s] %(message)s'
app.config['LOGGING_DIR'] = 'log'
app.config['LOGGING_FILENAME'] = f'app-{time_format}.log'
app.config['LOGGING_MAX_BYTES'] = 1024 * 1024
app.config['LOGGING_BACKUP_COUNT'] = 100
RequestID(app)

handler = logging.handlers.RotatingFileHandler(
    f"{app.config['LOGGING_DIR']}/{app.config['LOGGING_FILENAME']}",
    mode='a',
    maxBytes=app.config['LOGGING_MAX_BYTES'],
    backupCount=app.config['LOGGING_BACKUP_COUNT']
)
handler.addFilter(RequestIDLogFilter())
handler.setFormatter(Formatter(app.config['LOGGING_FORMAT']))
app.logger.setLevel(app.config['LOGGING_LEVEL'])
app.logger.addHandler(handler)

api = Api(app)

from flaskapp.views import namespaces

for namespace in namespaces:
    api.add_namespace(namespace)
