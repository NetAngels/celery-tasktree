#!/usr/bin/env python
from distutils.core import setup

setup(
    name='celery-tasktree',
    version='0.1',
    description='Celery Tasktree module',
    author='NetAngels team',
    author_email='info@netangels.ru',
    url='https://github.com/NetAngels/celery-tasktree',
    long_description = open('README.rst').read().decode('utf-8'),
    license = 'BSD License',
    py_modules=['celery_tasktree'],
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
)
