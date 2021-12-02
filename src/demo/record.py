"""
this class need to record some information when execute something such as start a activity or system related config
change
"""
import json
import time


class Recorder:
    def __init__(self):
        pass
    # TODO


APPEND = 'a'
WRITE = 'w'


def create_record_head(author, file_path, test_script_path=None, description=None):
    head = dict()
    head['author'] = author
    if test_script_path:
        head['test_script_path'] = test_script_path
    if description:
        head['description'] = description
    head['record_list'] = []
    json.dump(head, open(file_path, 'w'), ensure_ascii=False)


def record_action(
        action_name,
        file_path,
        device,
        xml,
        screen_shot_path=None,
        write_mode=APPEND,
        function_name=None,
        selector=None,
):
    file_content = json.load(open(file_path, 'r'))
    record = dict()
    record['action'] = action_name
    # record['action_result'] = action_result
    if selector:
        record['selector'] = selector
    if screen_shot_path and device:
        device.screenshot(screen_shot_path)
        # d.screenshot("home.jpg")
        record['screen_shot_path'] = screen_shot_path
    if screen_shot_path and not device:
        raise RuntimeError('not specify device')
    if function_name:
        record['trace'] = function_name
    record['current_info'] = device.app_current()
    record['time'] = time.time()
    record['xml'] = xml
    if write_mode == APPEND:
        file_content['record_list'].append(record)
    elif write_mode == WRITE:
        file_content['record_list'] = []
        file_content['record_list'].append(record)
    json.dump(file_content, open(file_path, 'w'))
