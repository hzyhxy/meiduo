from django.core.files.storage import Storage
from django.conf import settings
class FastDFSStorage(Storage):
    def _open(self):
        pass
    def _save(self):
        pass
    def url(self, name):
        '''
        拼接图片路径
        :param name:数据中存储的路径
        :return:
        '''
        return 'http://'+settings.HOST+':8888/' + name