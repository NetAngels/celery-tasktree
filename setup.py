#!/usr/bin/env python
import os
from distutils.core import setup

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return ''

setup(
    name='celery-tasktree',
    version='0.3.3',
    description='Celery Tasktree module',
    author='NetAngels team',
    author_email='info@netangels.ru',
    url='https://github.com/NetAngels/celery-tasktree',
    long_description = read('README.rst'),
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
