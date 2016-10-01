from marvinbot.celeryapp import marvinbot_app
from marvinbot.core import get_adapter
from celery.utils.log import get_task_logger


log = get_task_logger(__name__)
adapter = get_adapter()




