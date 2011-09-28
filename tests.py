# -*- coding: utf-8 -*-
"""
How to run these tests.
------------------------

1. Install celery, then copy ``celeryconfig.py.example`` to ``celeryconfig.py``
and tune the configuration file. Follow celery "getting started" guide:
http://docs.celeryproject.org/en/latest/getting-started/index.html
2. Launch celeryd as ``celeryd --loglevel=INFO``.
Make sure that tasks "test_tasks.mkdir" and "test_tasks.MkdirTask" are found.
3. Run tests with ``nosetests`` command.

"""
import os
from celery_tasktree import *
from nose.tools import *
from test_tasks import mkdir, MkdirTask

def setup():
    for dir in 'd1/2/1 d1/2/2 d1/2 d1/3 d1 d0/1/2 d0/1 d0/2 d0'.split():
        if os.path.isdir(dir):
            os.rmdir(dir)

@with_setup(setup, setup)
def test_task_tree():
    """
    Check TaskTree execution order.

    Following tree of tasks is created::

        d 0
        d 1 - d 1.1
            ` d 1.2 - d 1.2.1
            ` d 1.3 ` d 1.2.2
    """
    tree = TaskTree()

    # this set of tasks created in the right order should create all these
    # files
    node0 = tree.add_task(mkdir, args=['d0'])
    node1 = tree.add_task(mkdir, args=['d1'])
    node12 = node1.add_task(mkdir, args=['d1/2'])
    node13 = node1.add_task(mkdir, args=['d1/3'])
    node121 = node12.add_task(mkdir, args=['d1/2/1'])
    node122 = node12.add_task(mkdir, args=['d1/2/2'])

    # check that tree is build correctly
    eq_(tree.children, [node0, node1])
    eq_(node1.children, [node12, node13])
    eq_(node12.children, [node121, node122])
    eq_(node13.children, [])

    # run tasks and wait for the f0 and f1 task result
    async_res = tree.apply_async()
    f0_res, f1_res = async_res.join()
    eq_(f0_res.created, True)
    eq_(f1_res.created, True)

    # wait for the 1.1, 1.2, 1.3 task result
    f11_res, f12_res = f1_res.async_result.join()
    eq_(f11_res.created, True)
    eq_(f12_res.created, True)

    # wait for 1.2.1 and 1.2.2 tasks
    f121_res, f122_res = f11_res.async_result.join()
    eq_(f121_res.created, True)
    eq_(f122_res.created, True)

    # check that all files were created
    ok_(os.path.isdir('d1/2/1'))
    ok_(os.path.isdir('d1/2/2'))
    ok_(os.path.isdir('d1/3'))


@with_setup(setup, setup)
def test_task_already_contains_callback():
    tree = TaskTree()
    task0 = mkdir.subtask(args=['d0/1'])
    node0 = tree.add_task(mkdir, args=['d0'], kwargs=dict(callback=task0))
    node01 = node0.add_task(mkdir, args=['d0/2'])
    async_res = tree.apply_async()
    (f0_res,) = async_res.join()
    eq_(f0_res.created, True)
    f01_res, f02_res = f0_res.async_result.join()
    eq_(f01_res.created, True)
    eq_(f02_res.created, True)

@with_setup(setup, setup)
def test_task_subclass():
    tree = TaskTree()
    node0 = tree.add_task(MkdirTask, args=['d0'])
    node01 = node0.add_task(MkdirTask, args=['d0/1'])
    tree.apply_and_join()
    ok_(os.path.isdir('d0'))
    ok_(os.path.isdir('d0/1'))

@with_setup(setup, setup)
def test_push_and_pop():
    tree = TaskTree()
    tree.push(mkdir, args=('d0',))
    tree.push(mkdir, args=('d0/abc/def',))
    tree.pop()
    tree.push(mkdir, args=('d0/1',))
    tree.push(mkdir, args=('d0/1/2',))
    [res0, res1, res2] = tree.apply_and_join()

def test_empty_task_tree():
    tree = TaskTree()
    results = tree.apply_and_join()
    eq_(results, [])
