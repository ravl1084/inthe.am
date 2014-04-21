from django.conf import settings

from behave import given, when, then, step

from inthe_am.taskmanager.models import TaskStore


def get_store():
    return TaskStore.objects.get(user__email=settings.TESTING_LOGIN_USER)


@then(u'a task with the {field} "{value}" will exist')
def task_with_field_exists(context, field, value):
    store = get_store()
    matches = store.client.filter_tasks({
        field: value
    })
    assert len(matches) > 0, "No task found with %s == %s" % (
        field, value
    )


@given(u'an existing task with the {field} "{value}"')
def task_existing_with_value(context, field, value):
    store = get_store()
    basic_task = {
        'description': 'Gather at Terminus for Hari Seldon\'s Address',
        'project': 'terminus_empire',
        'tags': ['next_steps', 'mule'],
    }
    if field == 'tags':
        value = value.split(',')
    basic_task[field] = value
    task = store.client.task_add(**basic_task)
    context.created_task_id = task['uuid']


@then(u'a task named "{value}" is visible in the task list')
def task_with_description_visible(context, value):
    context.execute_steps(u'''
        then the element at CSS selector "{selector}" has text "{value}"
    '''.format(
        selector='div.task-list-item p.description',
        value=value
    ))


@then(u'a task named "{value}" is the opened task')
def task_with_description_visible_main(context, value):
    context.execute_steps(u'''
        then the element at CSS selector "{selector}" has text "{value}"
    '''.format(
        selector='h1.title',
        value=value
    ))
