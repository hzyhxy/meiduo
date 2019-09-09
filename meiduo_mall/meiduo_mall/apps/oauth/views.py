from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from QQLoginTool.QQtool import OAuthQQ
from django.http import JsonResponse, HttpResponse
from .models import OAuthQQUser
from django.contrib.auth import login
from itsdangerous import TimedJSONWebSignatureSerializer as TJS
from django_redis import get_redis_connection
from users.models import User
from django.utils.decorators import method_decorator
from django.contrib.auth.views import login_required
from celery_tasks.emaill.tasks import send_verify_email
import json
import re

# Create your views here.
class QQLoginView(View):
    def get(self, request):
        # next表示从哪个页面进入到的登录页面，将来登录成功的返回哪个页面
        next = request.GET.get('next')
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        login_url = oauth.get_qq_url()
        # 获取QQ登录页面网址
        return JsonResponse({'login_url': login_url})


class OAuthQQView(View):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return HttpResponse('缺少code')
        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET, redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 使用code向QQ服务器请求access_token
            access_token = oauth.get_access_token(code)
            # 使用access_token向QQ服务器请求openid
            openid = oauth.get_open_id(access_token)
            print(openid)
        except Exception as e:
            return HttpResponse('OAuth2.0认证失败')
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没绑定美多商城用户
            tjs = TJS(settings.SECRET_KEY, 5*60)
            openid = tjs.dumps(openid).decode()
            context = {'token': openid}
            print(context)
            return render(request, 'oauth_callback.html', context)
        else:
            # 如果openid已绑定美多商城用户
            # 实现状态保持
            qq_user = oauth_user.user
            login(request, qq_user)

            # 重定向到主页
            response = redirect('/index/')

            # 登录时用户名写入到cookie，有效期15天
            response.set_cookie('username', qq_user.username, max_age=3600*24815)
            return response
    def post(self, request):
            # 接收参数
            mobile = request.POST.get('mobile')
            pwd = request.POST.get('pwd')
            sms_code_client = request.POST.get('sms_code')
            access_token = request.POST.get('access_token')
            print(access_token)
            # next = request.GET.get('state')
            # if next is None:
            next = '/index/'

            # 校验参数
            # 判断参数是否齐全
            if not all([mobile, pwd, sms_code_client]):
                return  HttpResponse('缺少必填参数', status=400)
            # 判断手机号是否合法
            if not re.match(r'^1[3-9]\d{9}$', mobile):
                return HttpResponse('手机号格式不正确', status=400)
            # 判断密码是否合格
            if not re.match(r'^[0-9-A-Za-z]{8,20}$', mobile):
                return HttpResponse('请输入8-20位的密码', status=400)
            # 判断短信验证码是否一致
            redis_conn = get_redis_connection('verify_code')
            sms_code_server = redis_conn.get('sms_%s' % mobile)
            if sms_code_server is None:
                return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})
            if sms_code_client != sms_code_server.decode():
                return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入短信验证码有误'})
            # 判断openid是否有效：错误提示放在sms_code_errmsg位置
            # openid = check_access_tokecn(access_token)
            # 保存注册数据
            try:
                user = User.objects.get(mobile=mobile)
            except User.DoesNotExist:
                # 用户不存在，新建用户
                user = User.objects.create_user(username=mobile, password=pwd, mobile=mobile)
            else:
                # 如果用户存在，检查用户密码
                if not user.check_password(pwd):
                    return render(request, 'oauth_callback.html', {'account_errmsg': '用户名称或密码错误'})
            # 获取openid
            tjs = TJS(settings.SECRET_KEY, 5*60)
            openid = tjs.loads(access_token)
            # 将用户绑定openid
            try:
                OAuthQQUser.objects.create(openid=openid,user=user)
            except DatabaseError:
                return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})
            # 实现状态保持
            login(request, user)

            # 响应绑定结果
            response = redirect(next)
            # 登录时用户名写入到cookie，有效期15天
            response.set_cookie('username', user.username, max_age=3600*24*15)
            return response

@method_decorator(login_required,name='dispatch' )
class EmailView(View):
    def put(self, request):
        '''实现添加邮箱逻辑'''
        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return HttpResponse('缺少email参数', status=400)
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return  HttpResponse('参数email有误', status=400)
        # 赋值email字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            return JsonResponse({'{code}':5000, 'errmag': '添加邮箱失败'})
        # 异步发送验证邮件
        data = {'user_id': request.user.id, 'emaill': request.user.email}
        tjs = TJS(settings.SECRET_KEY, 5*60)
        token = tjs.dumps(data).decode()
        verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
        print(email, verify_url)
        send_verify_email.delay(email,verify_url)

        # 响应添加结果
        return JsonResponse({'code': 0, 'errmsg': '添加邮箱成功'})