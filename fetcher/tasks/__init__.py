# -*- coding: utf-8 -*-

from logging import getLogger

from fetcher.fetch import Extensions, Response, Request
from fetcher.utils import import_module


logger = getLogger('fetcher.tasks')


class Task(Extensions):
    '''Отдельная задача'''

    def __init__(self, **kwarg):
        self.no_cache_store = False
        self.no_cache_restore = False

        self.response = Response()
        self.request = Request()

        self.setup(**kwarg)

    def setup(self, **kwarg):
        '''Настройка параметров'''
        for name, value in kwarg.iteritems():
            if isinstance(value, Response):
                self.response = value.clone()
                continue
            if isinstance(value, Request):
                self.request = value.clone()
                continue
            if hasattr(self.request, name):
                setattr(self.request, name, value)
            else:
                setattr(self, name, value)
        return self

    def clone(self, **kwargs):
        '''Возвращает копию таска'''
        _kwargs = dict(
            (key, value)
            for key, value in self.__dict__.iteritems()
            if not key[0] == '_'
        )
        return Task(**_kwargs).setup(**kwargs)

    def process_response(self):
        '''Подготовка будущего запроса исходя из ответа'''
        self.request.url = self.response.url
        self.request.cookies.update(self.response.cookies)
        self.request.post = None
        self.request.method = 'GET'
        self.request.is_multipart_post = False


class TaskResult(dict):
    def __getattr__(self, name):
        return self[name]


class TasksGroup(object):
    '''Группа задач'''

    groups = {}

    def __init__(self, task, urls, **kwarg):
        TasksGroup.groups[id(self)] = self

        self.task = task
        self.count = len(urls)
        self.urls = urls
        self.errors = [None] * self.count
        self.finished_tasks = [None] * self.count
        self.setup(**kwarg)

    def __del__(self):
        TasksGroup.groups.pop(id(self), None)

    def setup(self, **kwarg):
        '''Настройка параметров'''
        for name, value in kwarg.iteritems():
            setattr(self, name, value)

    def produce_tasks(self):
        '''Генератор задач '''
        for index, url in enumerate(self.urls):
            yield Task(
                request=self.task.request.clone(
                    url=str(url)
                ),
                handler='group',
                group=id(self),
                index=index
            )


class Tasks(object):
    '''Менеджер задач'''

    def __init__(self, queue='memory', threads_count=20, **kwargs):
        '''
        Конструктор менеджера задач.
        Параметры:
            tasks_container - тип контейнера для хранения задач.
                Может принимать следующие значения: memory, mongo
        '''

        #self._queue = queue(**kwargs)

        if isinstance(queue, str):
            try:
                queue = import_module('fetcher.tasks.queues.%s' % queue).Queue
            except ImportError:
                raise Exception(u'Неудалось импортировать класс реализации очереди задач! Проверьте аргументы!')
        if queue:
            logger.info(u'Использование в качестве очереди задач %s' % queue)
            self._queue = queue(**kwargs)

        self._queue_size = threads_count * 2


    def add_task(self, task=None, **kwargs):
        '''
        Добавляет задачу в очередь.
        Если нужно, создает её по параметрам или устанавливает дополнительные
        параметры к существующей
        '''

        priority = kwargs.pop('priority', None) or \
                   getattr(task, 'priority', None) or \
                   100

        if task:
            task = task.clone()

        if len(kwargs) and task:
            task.setup(**kwargs)

        if not task:
            task = Task(**kwargs)

        self._queue.put((priority, task))

    def add_group(self, group=None, **kwargs):
        '''
        Добавление группы задач
        '''
        if not group:
            group = TasksGroup(**kwargs)

        for task in group.produce_tasks():
            self.add_task(task)

    def size(self):
        '''Размер очереди задач'''
        return self._queue.size()

    def get_task(self):
        '''Извлекает задачу'''
        return self._queue.get()

    def empty(self):
        '''Проверяет пустоту очереди'''
        return not self._queue.size()

    def full(self):
        '''Проверяет превышение *рекомендуемого* размера очереди'''
        return self._queue.size() == self._queue_size
