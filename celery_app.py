from celery import Celery

celery = Celery('your_project_name')
celery.config_from_object('celeryconfig')