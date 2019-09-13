from datetime import datetime

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse, HttpResponseForbidden, HttpResponseServerError

from .content_utils import get_categories, get_breadcrumb
from .models import SKU, GoodsChannel, ContentCategory, GoodsCategory, GoodsVisitCount
from django_redis import get_redis_connection
import  json


# Create your views here.
class ImageView(View):
    def get(self, request):
        sku = SKU.objects.all()
        print(sku)
        return HttpResponse('ok')


class IndexView(View):
    '''首页广告'''
    def get(self, request):
        '''提供首页广告界面'''
        # 查询商品频道和分类
        categories = get_categories()
        # 广告数据
        contents = {}
        contents_categories = ContentCategory.objects.all()
        for cat in contents_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')
        # 渲染模板的上下文
        context = {
            'contents': contents,
            'categories': categories
        }
        print(type(context['categories']))
        # print(type(categories))
        # for i in categories.values():
        #     print(i)
        return render(request, 'index.html', context)

class ListView(View):
    '''商品列表页'''
    def get(self, request, category_id, page_num):
        '''提供商品列表页'''
        # 判断category_id是否正确
        # print(category_id)
        # category_id= request.GET.get('cat')
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except :
            return HttpResponseNotFound('GoodsCategory does not exist')

        # 接收sort参数：如果用户不传，就是默认的排序规则
        sort = request.GET.get('sort', 'default')
        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category)
        # 按照排序规则查询该分类商品SKU信息
        if sort == 'price':
            # 按照价格由低到高
            sort_field = 'price'
        elif sort == 'hot':
            # 按照销量由高到底
            sort_field =  '-sales'
        else:
            sort_field = 'create_time'
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(sort_field)
        # 创建分页器：每页N条记录
        paginator = Paginator(skus, 5)
        # 获取每页商品数据
        try:
            page_skus = paginator.page(page_num)
        except:
            return HttpResponseNotFound('empty page')
        # 获取列表页总页数
        total_page = paginator.num_pages
        # 渲染页面
        context = {
            'categories': categories,
            'breadcrumb':breadcrumb,
            'sort': sort, # 排序字段
            'category': category, # 第三级分类
            'page_skus': page_skus, # 分页后的数据
            'total_page': total_page, # 总页数
            'page_num': page_num, # 当前页码
        }
        return render(request, 'list.html', context)


class HotGoodsView(View):
    '''商品热销排行榜'''
    def get(self, request, category_id):
        '''根据商品热销排行JSON数据'''
        # 根据销量倒序
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        # 序列化
        hot_sku_list = []
        for sku in skus:
            hot_sku_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': sku.price
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'hot_sku_list': hot_sku_list})


class DetailView(View):
    def get(self, request, sku_id):
        '''商品详情页'''
        try:
            sku = SKU.objects.get(id=sku_id)
        except:
            return render(request, '404.html')
        # 查询商品频道分类
        categories = get_categories()
        # 查询面包屑导航
        breadcrumb = get_breadcrumb(sku.category)
        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的的规格不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options
        print(sku.spu.desc_detail)
        #渲染页面
        context = {
            'categories': categories,
            'breadcrumb':breadcrumb,
            'sku':sku,
            'spu': sku.spu,
            'category_id': sku.category.id
            # 'specs': goods_specs,
        }
        return render(request, 'detail.html', context)


class DetailVisitView(View):
    def post(self, requets, category_id):
        '''记录分类商品访问量'''
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except:
            return HttpResponseForbidden('缺少必传参数')

        # 获取今天的日期
        t = datetime.now()
        today_str = '%d-%02d-%2d' %(t.year, t.month, t.day)
        today_date = datetime.strptime(today_str,'%Y-%m-%d')
        try:
            # 查询今天该类别商品的访问量
            counts_data = category.goodsvisitcount_set.get(date=today_date)
        except:
            # 如果该类别的商品在今天没有过访问记录，就是新建一个访问记录
            counts_data = GoodsVisitCount()
        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.save()
        except:
            return HttpResponseServerError('服务器异常')
        return  JsonResponse({'code': 0, 'errmsg': 'ok'})


class HistoriesView(View):
    def get(self, request):
        '''获取用户浏览记录'''
        # 获取Redis存储的sku_id列表信息
        redis_conn = get_redis_connection()
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0 , -1)
        # 根据sku_id列表数据，查询出商品sku信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
            return JsonResponse({'code': 0, 'errmsg': 'ok', 'skus': skus})
    def post(self, request):
        '''保存用户浏览记录'''
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 校验参数
        try:
            SKU.objects.get(sku_id)
        except:
            return HttpResponseNotFound('该用户不存在')
        # 保存用户浏览数据
        redis_conn = get_redis_connection('history')
        p1 = redis_conn.pipline()
        user_id = request.user.id
        # 先去重
        p1.lrem('history_%s' % user_id ,0, sku_id )
        # 再储存
        p1.lpush('history_%s' % user_id, sku_id)
        # 最后截取
        p1.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        p1.execute()

        # 响应结果
        return JsonResponse({'code': 0, 'errms': 'ok'})