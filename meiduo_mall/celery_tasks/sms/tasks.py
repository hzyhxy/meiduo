from ..main import celery_app
from meiduo_mall.libs.yuntongxun.sms import CCP
@celery_app.task(name='ccp_send_sms_code')
def ccp_send_sms_code():
    print(111)
    # 发送短信验证码
    # CCP().send_template_sms(mobile, [sms_code, 5*60], 1)
    CCP()