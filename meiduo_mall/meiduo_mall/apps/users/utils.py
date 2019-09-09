from django.contrib.auth.backends import ModelBackend
import re
from .models import User

def get_user_by_accoutn(account):
    try:
        if re.match('^1[3-9]\d{9}$', account):
            # 手机号登录
            user = User.objects.get(mobile=account)
        else:
            # 用户名登录
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user

class UsernameMobileAuthBackend(ModelBackend):
    '''自定义用户认证后端'''
    def authenticate(self ,request, username=None, password=None,**kwargs ):
        '''重写认证方法，实现多账号登录'''
        # 根据传入的username获取usr对象，usernam可以是手机号也可以是账号
        user = get_user_by_accoutn(username)
        # 校验user是否存在并校验密码是否正确
        if user and user.check_password(password):
            return user