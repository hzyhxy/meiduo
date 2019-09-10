from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, HttpResponseNotFound

from .content_utils import get_categories, get_breadcrumb
from .models import SKU, GoodsChannel, ContentCategory, GoodsCategory

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
        print(skus)
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
        print(1)
        return render(request, 'list.html', context)
