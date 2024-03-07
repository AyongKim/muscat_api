FROM python:3.9-slim

ENV ALL_CLASS_HOME="/home/allclass"
ENV ALL_CLASS_USER="allclass"

COPY requirements.txt /tmp/requirements.txt

RUN pip install -U pip &&\
    pip install -r /tmp/requirements.txt

RUN useradd -ms /bin/bash ${ALL_CLASS_USER}

COPY --chown=${ALL_CLASS_USER}:${ALL_CLASS_USER} entrypoint.sh ${ALL_CLASS_HOME}/
RUN chmod 744 ${ALL_CLASS_HOME}/entrypoint.sh

COPY src ${ALL_CLASS_HOME}/src
RUN chown -R ${ALL_CLASS_USER}:${ALL_CLASS_USER} ${ALL_CLASS_HOME}/src

RUN mkdir -p ${ALL_CLASS_HOME}/log
RUN chown -R ${ALL_CLASS_USER}:${ALL_CLASS_USER} ${ALL_CLASS_HOME}/log

USER ${ALL_CLASS_USER}
WORKDIR ${ALL_CLASS_HOME}

ENTRYPOINT ["./entrypoint.sh"]
