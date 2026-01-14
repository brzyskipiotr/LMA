#!/bin/bash
gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout=120 app.main:app -k uvicorn.workers.UvicornWorker
