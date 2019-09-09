# 设置django配置
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "meiduo_mall.settings.dev"

# celery启动文件
from celery import Celery

# 创建celery实例
celery_app = Celery('meiduo')
# 加载celery配置
celery_app.config_from_object('celery_tasks.config')
# 自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.emaill'])