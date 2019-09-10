from .models import GoodsChannel
from collections import OrderedDict
def get_categories():
    categories = OrderedDict()
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        group_id = channel.group_id  # 当前组
        if group_id not in categories:
            categories[group_id] = {'channels': [], 'sub_cats': []}
        cat1 = channel.category  # 当前频道的类别
        # 追加当前频道
        categories[group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url,
        })
        # 构建当前类别的子类别
        for cat2 in cat1.subs.all():
            cat2.sub_cats = []
            for cat3 in cat2.subs.all():
                cat2.sub_cats.append({
                    'id': cat3.id,
                    'name': cat3.name,
                })
            categories[group_id]['sub_cats'].append({
                'id': cat2.id,
                'name': cat2.name,
                'sub_cats': cat2.sub_cats,
            })

    return categories


def get_breadcrumb(category):
    '''
    获取面包屑
    :param category:
    :return:
    '''
    breadcrumb = dict(
        cat1 = '',
        cat2 = '',
        cat3 = ''
    )
    if category.parent is None:
        # 当前类别为以及类别
        breadcrumb['cat1'] = category
    elif category.subs.count() == 0:
        # 当前类别为三级
        breadcrumb['cat3'] = category
        cat2 = category.parent
        breadcrumb['cat2'] = cat2
        breadcrumb['cat1'] = cat2.parent
    else:
        # 当前类别为二级
        breadcrumb['cat2'] = category
        breadcrumb['cat1'] = category.parent
    cat1 = breadcrumb['cat1']
    breadcrumb['cat1'] = {
        'url': cat1.goodschannel_set.all()[0].url,
        'name': cat1.name
    }
    return breadcrumb