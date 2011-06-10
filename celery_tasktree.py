# -*- coding: utf-8 -*-
from celery.task import task
from celery.task.sets import TaskSet
from functools import wraps


class TaskTree(object):

    def __init__(self):
        self.children = []

    def add_task(self, func, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        node = TaskTreeNode(func, args, kwargs)
        self.children.append(node)
        return node

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
            task = func.subtask(args=args, kwargs=kwargs)
            tasks.append(task)
        taskset = TaskSet(tasks)
        result = taskset.apply_async()
        return result


class TaskTreeNode(object):

    def __init__(self, func, args=None, kwargs=None):
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
            task = func.subtask(args=args, kwargs=kwargs)
            tasks.append(task)
        return tasks


def task_with_callbacks(func):
    """ decorator "task with callbacks"

    Callback or list of callbacks which go to function in "callbacks" kwarg,
    will be executed after the function, regardless of the subtask's return
    status.

    If subtask (function) result is an object, then a property named
    "async_result" will be added to that object so that it will be possible to
    join() for that result.
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
    return task(wrapper)


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
