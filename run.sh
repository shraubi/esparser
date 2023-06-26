#!/bin/bash
set -a
. /app/.env
set +a
export PYTHONPATH='/app'
/usr/local/bin/python3 /app/scrapers/upwork.py
