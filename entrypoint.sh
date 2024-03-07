#!/bin/bash

HOST="0.0.0.0"
PORT="1001"

core_count=$(python3 -c """
import multiprocessing
print(multiprocessing.cpu_count())
""" )
WORKER_COUNT=$((core_count * 2))

export PYTHONPATH="./src:$PYTHONPATH"

echo "Worker count : ${WORKER_COUNT}"
echo "Host : ${HOST}"
echo "Port : ${PORT}"

gunicorn -b ${HOST}:${PORT} -w "${WORKER_COUNT}" --timeout=10 flaskapp:app
