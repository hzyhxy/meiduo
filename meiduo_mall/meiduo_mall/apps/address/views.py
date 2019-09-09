from django.shortcuts import render
from django.views import View
from .models import Area
from users.models import Address
from django.http import JsonResponse,HttpResponse
import json
import re

# Create your views here.
class AddressesView(View):
    def get(self, request):
        '''提供用户地址列表'''
        # 获取用户地址列表
        user = request.user
        addresses = Address.objects.filter(user=user, is_deleted=False)
        addresses_list = []
        for address in addresses:
            addresses_list.append({
                'id': address.id,
                'receiver': address.receiver,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'mobile': address.mobile,
                'tel': address.tel,
                'email': address.email,
                'title':address.title
            })

        return render(request, 'user_center_site.html', {'addresses': addresses_list})
        # return HttpResponse(context)

    def put(self, request, address_id):
        '''修改地址'''
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('emaill')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponse('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}', mobile):
            return HttpResponse('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9)]{1,4})?$', tel):
                return HttpResponse('参数tel有误')
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponse('参数email有误')
        # 判断地址是否存在，并更细地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email='',
            )
        except Exception as e:
            return JsonResponse({'code': -1, 'errmsg': '更新地址失败'})
        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province': address.province.name,
            'province_id': address.province_id,
            'city': address.city.name,
            'city_id': address.city_id,
            'district': address.district.name,
            'district_id': address.district_id,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'emaill': address.email
        }
        # print(address_dict)
        # 响应更细地址结果
        return JsonResponse({'code': 0, 'address': address_dict})
    def delete(self, request, address_id):
        '''删除地址'''
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            return JsonResponse({'code': -1, 'errnsg': '删除地址失败'})
        # 响应删除地址结果
        return JsonResponse({'code': 0, 'errmsg': '删除地址成功'})

class AreasView(View):
    '''省市区数据'''
    def get(self, request):
        '''提供省市区数据'''
        area_id = request.GET.get('area_id')
        if not area_id:
            # 提供省份数据
            try:
                province_model_list = Area.objects.filter(parent__isnull=True)

                # 序列化省级数据
                province_list = []
                for province_model in province_model_list:
                    province_list.append({'id': province_model.id, 'name': province_model.name})
            except Exception as e:
                return JsonResponse({'code': -1, 'errmsg': '城市或区数据错误'})
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'province_list': province_list})
        else:
            # 提供市或区数据
            try:
                parent_model = Area.objects.get(id=area_id) # 查询市或区的父级
                sub_model_list = parent_model.subs.all()

                # 序列化市或区数据
                sub_list = []
                for sub_model in sub_model_list:
                    sub_list.append({'id': sub_model.id, 'name': sub_model.name})
                sub_data = {
                    'id': parent_model.id,  # 父级pk
                    'name': parent_model.name,  # 父级name
                    'subs': sub_list  # 父级的子集
                }
            except Exception as e:
                return JsonResponse({'code': -1, 'errmsg': '城市或区数据错误'})
            # 响应市或区数据
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'sub_data': sub_data})


class CreateAddressView(View):
    def post(self, request):
        '''实现新增地址逻辑'''
        # 判断是否超过地址上限：最多20个
        # Address.objects.filter(suer=request.user).count()
        count = request.user.addresses.count()
        if count >= 20:
            return JsonResponse({'code': -1, 'errmsg': '超过地址数量上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        emaill = json_dict.get('emaill')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponse('缺少必填参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponse('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponse('参数tel有误')

        # 保存地址信息
        try:
            address = Address.objects.create(user=request.user, title=receiver, receiver=receiver, province_id=province_id, city_id=city_id, district_id=district_id, place=place,mobile=mobile, tel=tel, email='')
            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            return  JsonResponse({'code': -1, 'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        address_dict = {
            'code': 0,
            'errmsg': 'ok',
            'id': address.id,
            'receiver': address.receiver,
            'province': address.province.name,
            'province_id': address.province_id,
            'city': address.city.name,
            'city_id': address.city_id,
            'district': address.district.name,
            'district_id':address.district_id,
            'place': address.place,
            'mobile': mobile,
            'tel': tel,
            'email': emaill
        }
        # 响应保存结果
        return JsonResponse({'code': 0, 'errmsg':'新增地址成功', 'address': address_dict})


class DefaultAdressesView(View):
    def put(self, request, address_id):
        '''设置默认地址'''
        try:
            # 接收参数，查询地址
            address = Address.objects.get(id = address_id)
            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception:
            return JsonResponse({'code': -1, 'errmsg': '设置默认地址失败'})
    # 响应设置默认地址结果
        return JsonResponse({'code': 0, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(View):
    def put(self, request, address_id):
        '''设置标题'''
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        try:
            # 查询地址
            addresses = Address.objects.get(id=address_id)

            # 设置新的标题
            addresses.title = title
            addresses.save()
        except Exception:
            return JsonResponse({'code': -1, 'errmsg': '设置标题失败'})
        # 4.响应设置地址结果
        return JsonResponse({'code': 0, 'errmsg': '设置地址标题成功'})