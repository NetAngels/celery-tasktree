# -*- coding: utf-8 -*-
from celery.task import Task
from celery_tasktree import task_with_callbacks, run_with_callbacks
import os


@task_with_callbacks
def mkdir(directory):
    """ Create directory.

    We return CreateDirectoryResult object intentionally, so that
    task_with_callbacks decorator can add async_result attribute to this one.
    """
    os.mkdir(directory)
    return CreateDirectoryResult(True)


class MkdirTask(Task):

    @run_with_callbacks
    def run(self, directory):
        os.mkdir(directory)
        return CreateDirectoryResult(True)


class CreateDirectoryResult(object):
    def __init__(self, created):
        self.created = created
    def __bool__(self):
        return bool(self.created)
    def __str__(self):
        return '%s <%s>' % (id(self), self.created)
