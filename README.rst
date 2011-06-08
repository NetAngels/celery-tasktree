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
