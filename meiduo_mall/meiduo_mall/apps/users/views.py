from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from .models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.views import login_required
import re
# Create your views here.
from django_redis import get_redis_connection
def index(request):
    return render(request, 'index.html')

class regiter(View):
    def get(self, request):
        return render(request, 'register.html')
    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        password2 = request.POST.get('cpwd')
        mobile = request.POST.get('phone')
        sms_code  = request.POST.get('msg_code')
        allow = request.POST.get('allow')
        print(username, password, password2, mobile, sms_code, allow)
        user = User.objects.filter(username=username)
        # print(user)
        if user:
            return HttpResponse("此用户已存在", status=400)
        if (username is None) or (password is None) or (password2  is None) or (mobile is None) or (sms_code is None) or (allow is None):
            return HttpResponse('填写数据不完整', status=400)
        if len(username) <5 or len(username) >20:
            return HttpResponse('用户长度不符合要求', status=400)
        if not re.match(r'[0-9]{8,10}', password):
            return HttpResponse('密码长度不符合要求', status=400)
        if password != password2:
            return HttpResponse('两次密码输入不一致', status=400)
        if len(mobile) != 11:
            return HttpResponse('手机号错误', status=400)
        # 接收短信验证码参数
        # print(request.POST.get('sms_code'))
        # 保存注册数据之前，对比短信验证码
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' %mobile)
        print(sms_code_server)
        if sms_code_server is None:
            print(sms_code_server)
            return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})
        if sms_code_server.decode() != sms_code:
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})
        User.objects.create_user(username=username, password=password, mobile=mobile)

        return redirect('/index/')

class LoginView(View):
    def get(self, request):
        '''
        提供登录页面
        :param request: 
        :return: 
        '''
        return render(request, 'login.html')
    def post(self, request):
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remembered = request.POST.get('remembered')

        # 校验参数
        # 判断参数是否齐全
        if not all([username, password]):
            return  HttpResponse('缺少必传参数', status=400)
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[0-9A-Za-z-]{5,20}', username):
            return HttpResponse('请输入正确的用户名', status=400)
        # 认证登录用户
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 实现状态保持
        login(request, user)
        # 设置状态保持的周期
        if remembered != 'on':
            # 没有记住用户，浏览器会话结束就过期
            request.session.set_expiry(0)
        else:
            # 记住用户：None表示两周后就过期
            request.session.set_expiry(None)
        response = redirect('/index/')
        response.set_cookie('username',request.user.username)
        print(request.user.username)
        # 响应登录结果
        return response


class LogOutView(View):
    def get(self, request):
        logout(request)
        response = redirect('/login/')
        response.delete_cookie('username')
        return response

@method_decorator(login_required,name='dispatch' )
class InfoView(View):
    def get(self, request):
        context = {

        }
        return render(request, 'user_center_info.html', context)


class ChangePasswordView(View):
    def get(self ,request):
        return render(request, 'user_center_pass.html')
    def post(self, request):
        '''实现修改密码逻辑'''
        # 获取接收参数
        old_password = request.POST.get('old_pwd')
        new_password = request.POST.get('new_pwd')
        new_password2 = request.POST.get('new_cpwd')
        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return HttpResponse('参数输入不完整')
        if not request.user.check_password(old_password):
            return HttpResponse('原始密码输入不正确')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            # '^ [0 - 9A - Za - z]{8, 20}$'
            return HttpResponse('新密码复杂度不符合要求')
        if new_password != new_password2:
            return HttpResponse('两次密码输入不一致')
        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception:
            return JsonResponse({'code':-1, 'errmsg': '密码设置失败'})
        # 清理状态能保持信息
        logout(request)
        response = redirect('/login/')
        response.delete_cookie('username')
        return response