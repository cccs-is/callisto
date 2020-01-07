release: python manage.py migrate
web: gunicorn hub.wsgi --log-file -
#worker: celery worker -A datauploader --concurrency 1
