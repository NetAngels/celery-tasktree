Celery tasktree module
======================

celery-tasktree is a module which helps to execute trees of celery tasks
asynchronously in a particular order. Tasktree comes to the rescue when a
number of tasks and dependencies grows and when naive callback-based approach
becomes hard to understand and maintain.

Usage sample
-------------

::

    from tasktree import task_with_callbacks, TaskTree

    @task_with_callbacks
    def some_action(...):
        ...

    def execute_actions():
        tree = TaskTree()
        task0 = tree.add_task(some_action, args=[...], kwargs={...})
        task1 = tree.add_task(some_action, args=[...], kwargs={...})
        task10 = task1.add_task(some_action, args=[...], kwargs={...})
        task11 = task1.add_task(some_action, args=[...], kwargs={...})
        task110 = task11.add_task(some_action, args=[...], kwargs={...})
        async_result = tree.apply_async()
        return async_result


Decorator named ``task_with_callbacks`` should be used instead of simple celery
``task`` decorator.

According to the code:

- task0 and task1 are executed simultaniously
- task10 and task11 are executed simultaniously after task1
- task110 is executed after task11

Things to be noted:

- There is no way to stop propagation of the execution and there is no way to
  pass extra arguments from ancestor to child task. In short, there in only one
  kind of dependency between tasks: the dependency of execution order.
- If subtask (function) return value is an object, then a property named
  "async_result" will be added to that object so that it will be possible to
  join() for. To extend previous example::

      async_result = execute_actions() 
      task0_result, task1_result = async_result.join()
      task10_result, task11_result = task1_result.async_result.join()
      task110_result = task11_result.async_result.join() 

Using TaskTree as a simple queue
-----------------------------------

In many cases a fully fledged tree of tasks would be overkill for you. All you
need is to add two or more tasks to a queue to make sure that they will be
executed in order. To make it happens TaskTree has ``push()`` and ``pop()``
methods which in fact are nothing but wrappers around ``add_task()``.
The ``push()`` method adds a new task as a child to the perviously created one
whereas ``pop()`` removes and returns the task from the tail of the task stack.
Usage sample looks like::

    # create the tree
    tree = TaskTree()
    # push a number of tasks into it
    tree.push(action1, args=[...], kwargs={...})
    tree.push(action2, args=[...], kwargs={...})
    tree.push(actionX, args=[...], kwargs={...})
    tree.pop() # get back action X from the queue
    tree.push(action3, args=[...], kwargs={...})
    # apply asynchronously
    tree.apply_async()

Actions will be executed in order ``action1 -> action2 -> action3``.


Task with callbacks outside TaskTree
---------------------------------------

``task_with_callbacks`` decorator can be useful in itself. It decorates
functions the same way as ordinary ``task`` celery decorator does, but also
adds an optional ``callback`` parameter.

Callback can be a subtask or a list of subtasks (not the TaskSet). Behind the
scene, when a task with callback is invoked, it executes function's main code,
then builds a TaskSet, invokes it asynchronously and attaches the
``TaskSetResut`` as the attribute named ``async_result`` to function's return
value.

Simple example is provided below::

    from tasktree import task_with_callbacks

    @task_with_callbacks
    def some_action(...):
        ...

    cb1 = some_action.subtask(...)
    cb2 = some_action.subtask(...)
    async_result = some_action.delay(..., callback=[cb1, cb2])
    main_result = async_result.wait()
    cb1_result, cb2_result = main_result.async_result.join()
