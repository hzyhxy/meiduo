from django.shortcuts import render
from django.views import View
from users.models import User
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.http import HttpResponse
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from django.conf import settings
from users.models import User


import logging
import random
# 准备captcha包
from meiduo_mall.libs.captcha.captcha import Captcha
from celery_tasks.sms.tasks import ccp_send_sms_code

# Create your views here.
class UserName(View):
    def get(self, request,username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'count': count})


class Mobile(View):
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'count': count})

# 图形验证码视图
class ImageCode(View):
    def get(self, request, uuid):
        # 生成验证码
        # print(uuid)
        captcha = Captcha.instance()
        _,data,image = captcha.generate_captcha()
        # 保存验证码
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('image_%s'%uuid, 60*5, data)
        print(redis_conn.get('image_%s'%uuid))
        # 响应验证码
        return HttpResponse(image, content_type='image/jpg')

class SmsCode(View):
    def get(self, request, mobile):
        client = get_redis_connection('verify_code')
        send_flag = client.get('sms_flag_%s'%mobile)
        if send_flag:
            return JsonResponse({'code': 4002, 'errmsg': '发送短信过于频繁'})
        # 接收参数
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        print(image_code, uuid)
        # 校验参数
        if not all([image_code, uuid]):
            return JsonResponse({'code': 4002, 'errmsg': '缺少必填参数'})
        # 验证图片验证码
        # c创建连接到redis的对象
        imgage_code_server = client.get('image_%s'%uuid)
        if imgage_code_server is None:
            return JsonResponse({'code': 4001, 'errmsg': '图形验证码失效'})
        # 删除图形验证码，避免恶意测试图形验证码
        # try:
        #      client.delete('img_%s'%uuid)
        # except Exception as e:
        #     logging.error(e)
        # 对比图形验证码
        imgage_code_server = imgage_code_server.decode()
        if imgage_code_server.lower() != image_code.lower():
            return JsonResponse({'code': 4001, 'errmsg': '输入验证码有误'})
        # 生成短信验证码：生成六位数的短信验证码
        sms_code = '%06d' %random.randint(0, 999999)
        ccp_send_sms_code.delay()
        # 创建Redis管道
        p1 = client.pipeline()
        # 将Reids请求添加到队列
        p1.setex('sms_%s' % mobile, 5*60, sms_code)
        # 重新写入send_flag
        p1.setex('sms_flag_%s'%mobile, 1*60, 1)
        # 执行请求
        p1.execute()
        print(sms_code)
        #返回响应
        return JsonResponse({'code':0, 'errmsg':'发送短信成功'})


class EmailsVerify(View):
    def get(self, request):
        data = request.GET
        token = data.get('token')
        tjs = TJS(settings.SECRET_KEY, 5*60)
        try:
            token = tjs.loads(token)
        except:
            return HttpResponse("验证已失效")
        try:
            user_id = token['user_id']
            emaill = token['emaill']
            print(user_id)
        except Exception:
            return HttpResponse("验证失败！")
        try:
            user = User.objects.get(id=user_id)
            user.email_active = 1
            user.save()
        except:
            return HttpResponse("用户不存在")
        return render(request, 'user_center_info.html')

