from __future__ import print_function

from collections import Counter
import json
import os
import string
from urlparse import urljoin
import uuid

from django.conf import settings
from django.contrib.auth.models import User
import lxml.html
import requests
from splinter.browser import Browser


TEST_COUNTERS = {
    'following': Counter(),
    'before': Counter(),
    'demand': Counter()
}
ABSOLUTE_COUNTER = 0


def sanitize_name(name):
    acceptable_letters = []
    for char in name:
        if char in string.letters:
            acceptable_letters.append(char)
        if char == ' ':
            acceptable_letters.append('_')
    return ''.join(acceptable_letters)


def calculate_absolute_path(context, url):
    server_url = context.config.server_url

    if '://' in url:
        return url
    elif url.startswith('/'):
        return server_url + url.lstrip('/')

    return server_url + url


def save_full_page_details(context, output_path):
    try:
        js_errors = {
            'result': json.loads(
                context.browser.evaluate_script(
                    "JSON.stringify(JS_ERRORS);"
                )
            )
        }
    except Exception as e:
        print(e)
        js_errors = {'error': str(e)}

    try:
        console_log = {
            'result': json.loads(
                context.browser.evaluate_script(
                    "JSON.stringify(CONSOLE_LOG);"
                )
            )
        }
    except Exception as e:
        print(e)
        console_log = {'error': str(e)}

    metadata = {
        'js_errors': js_errors,
        'console_log': console_log,
    }

    with open(os.path.join(output_path, 'meta.json'), 'w') as out:
        out.write(
            json.dumps(metadata).encode('utf8')
        )

    document = lxml.html.document_fromstring(
        context.browser.html
    )
    resource_urls = {}
    # Rewrite dom assets
    selectors = [
        ('//script', 'src', ),
        ('//link', 'href', ),
        ('//img', 'src', ),
    ]
    for selector, attribute in selectors:
        for result in document.xpath(selector):
            src = result.attrib.get(attribute)
            if not src:
                continue

            url = calculate_absolute_path(context, src)
            if url not in resource_urls:
                _, extension = os.path.splitext(url)
                resource_urls[url] = str(uuid.uuid4()) + extension
            result.attrib[attribute] = resource_urls[url]

    with open(os.path.join(output_path, 'index.html'), 'w') as out:
        out.write(lxml.html.tostring(document))

    for asset_url, name in resource_urls.items():
        with open(os.path.join(output_path, name), 'w') as out:
            try:
                out.write(
                    requests.get(asset_url, timeout=5).content
                )
            except Exception as e:
                out.write(str(e))


def save_page_details(context, step=None, prefix='demand'):
    global TEST_COUNTERS, ABSOLUTE_COUNTER
    ABSOLUTE_COUNTER += 1

    this_absolute_counter = ABSOLUTE_COUNTER

    scenario_name = sanitize_name(context.scenario.name)
    if step:
        step_name = sanitize_name(step.name)
    else:
        step_name = ''

    status = 'FAIL' if context.failed else 'OK'

    TEST_COUNTERS[prefix][scenario_name] += 1
    this_counter = TEST_COUNTERS[prefix][scenario_name]

    name = '{absolute}_{scenario}_{num}_{step}_{prefix}_{status}'.format(
        absolute=str(this_absolute_counter).zfill(5),
        scenario=scenario_name,
        num=str(this_counter).zfill(2),
        step=step_name,
        prefix=prefix,
        status=status,
    )

    context.browser.screenshot(name)
    with open(os.path.join('/tmp', name + '.html'), 'w') as out:
        out.write(context.browser.html.encode('utf-8'))

    if context.failed or settings.TEST_ALWAYS_SAVE_FULL_PAGE_DETAILS:
        full_path = os.path.join('/tmp', name)
        do_save = False
        try:
            os.mkdir(full_path)
            do_save = True
        except Exception as e:
            print(
                "Error encountered when saving full page details: %s" % e
            )

        if do_save:
            save_full_page_details(context, full_path)


def before_all(context):
    context.engine = getattr(settings, 'WEBDRIVER_BROWSER', 'phantomjs')
    # Ember is running on :8000, and it knows to send API traffic to :8001
    # where this server is running.
    context.config.server_url = 'http://127.0.0.1:8000/'
    context.browser = Browser(context.engine)
    context.browser.driver.set_window_size(1024, 800)
    context.browser.driver.implicitly_wait(10)
    context.browser.driver.set_page_load_timeout(60)
    context.browser.visit(context.config.server_url)
    context.browser.execute_script(
        u"window.localStorage.setItem('disable_ticket_stream', 'yes');"
    )


def after_all(context):
    context.browser.quit()
    context.browser = None


def before_step(context, step):
    if 'TRAVIS' in os.environ:
        try:
            save_page_details(context, step, 'before')
        except Exception as e:
            print(e)


def after_step(context, step):
    if 'TRAVIS' in os.environ:
        try:
            save_page_details(context, step, 'following')
        except Exception as e:
            print(e)


def before_scenario(context, step):
    if hasattr(settings, 'TESTING_LOGIN_USER'):
        User.objects.filter(
            email=settings.TESTING_LOGIN_USER
        ).delete()


def after_scenario(context, step):
    if hasattr(context, 'teardown_steps'):
        for teardown_function in context.teardown_steps:
            teardown_function(context)
        context.teardown_steps = []

    context.browser.visit(urljoin(context.config.server_url, '/logout/'))
