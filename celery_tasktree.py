# -*- coding: utf-8 -*-
from celery.task import task
from celery.task.sets import TaskSet
from functools import wraps


class TaskTree(object):

    def __init__(self):
        self.children = []
        self.last_node = self

    def add_task(self, func, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        node = TaskTreeNode(func, args, kwargs)
        self.children.append(node)
        node.parent = self
        return node

    def push(self, func, args=None, kwargs=None):
        self.last_node = self.last_node.add_task(func, args, kwargs)
        return self.last_node

    def pop(self):
        if self.last_node == self:
            raise IndexError('pop from empty stack')
        parent = self.last_node.parent
        parent.children.remove(self.last_node)
        self.last_node = parent

    def apply_async(self):
        tasks = []
        for node in self.children:
            func = node.func
            args = node.args
            kwargs = node.kwargs
            callback = kwargs.pop('callback', [])
            if not isinstance(callback, (list, tuple)):
                callback = [callback]
            subtasks = node._get_child_tasks()
            callback += subtasks
            kwargs = dict(callback=callback, **kwargs)
            _task = func.subtask(args=args, kwargs=kwargs)
            tasks.append(_task)
        taskset = TaskSet(tasks)
        result = taskset.apply_async()
        return result

    def apply_and_join(self):
        """ Execute tasks asynchronously and wait for the latest result.

        Method can be useful in conjunction with pop()/push() methods. In such
        a case method returns a list of results in the order which corresponds
        to the order of nodes being pushed.
        """
        return join_tree(self.apply_async())


def join_tree(async_result):
    """ Join to all async results in the tree """
    output = []
    results = async_result.join()
    if not results:
        return output
    first_result = results[0]
    while True:
        output.append(first_result)
        if not getattr(first_result, 'async_result', None):
            break
        first_result = first_result.async_result.join()[0]
    return output


class TaskTreeNode(object):

    def __init__(self, func, args=None, kwargs=None):
        self.parent = None
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.children = []

    def add_task(self, func, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        node = TaskTreeNode(func, args, kwargs)
        self.children.append(node)
        node.parent = self
        return node

    def _get_child_tasks(self):
        tasks = []
        for node in self.children:
            func = node.func
            args = node.args
            kwargs = node.kwargs
            callback = kwargs.pop('callback', [])
            if not isinstance(callback, (list, tuple)):
                callback = [callback]
            subtasks = node._get_child_tasks()
            callback += subtasks
            kwargs = dict(callback=callback, **kwargs)
            _task = func.subtask(args=args, kwargs=kwargs)
            tasks.append(_task)
        return tasks


def task_with_callbacks(func, **options):
    """ decorator "task with callbacks"

    Callback or list of callbacks which go to function in "callbacks" kwarg,
    will be executed after the function, regardless of the subtask's return
    status.

    If subtask (function) result is an object, then a property named
    "async_result" will be added to that object so that it will be possible to
    join() for that result.
    """
    return task(run_with_callbacks(func), **options)


def run_with_callbacks(func):
    """Decorator "run with callbacks"

    Function is useful as decorator for :meth:`run` method of tasks which are
    subclasses of generic :class:`celery.task.Task` and are expected to be used
    with callbacks.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        callback = kwargs.pop('callback', None)
        retval = func(*args, **kwargs)
        async_result = _exec_callbacks(callback)
        try:
            retval.async_result = async_result
        except AttributeError:
            pass
        return retval
    return wrapper


def _exec_callbacks(callback):
    """ Exec the callback or list of callbacks. Return asyncronous results as
    the TaskSetResult object.
    """
    async_result = None
    if callback:
        if not isinstance(callback, (list, tuple)): # not iterable
            callback = [callback,]
        taskset = TaskSet(tasks=callback)
        async_result = taskset.apply_async()
    return async_result
