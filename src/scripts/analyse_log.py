import os
import re
import csv
import json

import PIL
from tqdm import tqdm
from PIL import Image
from collections import namedtuple


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


benchmark = '/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark'
ablation = '/Users/pkun/PycharmProjects/ui_api_automated_test/ablation'
# apps = ['chrome', 'contact', 'gmail', 'photo', 'setting', 'clock']
apps = list(filter(lambda x: os.path.isdir(os.path.join(benchmark, x)), os.listdir(benchmark)))
TIME = re.compile(r'\d+-\d+-(\d+) (\d+):(\d+):\d+')
STATEMENT = re.compile(r'd\(.*\).*')
SCREENSHOT = re.compile(r'screenshot is (\d+.png)')
MATCH_WIDGET = re.compile(r'executor - INFO - match widget ')
DESCRIPTION = re.compile('generating event for "(.*)"')
format_time = namedtuple('format_time', ['day', 'hour', 'minute'])
data_header = ['app', 'filename', 'time', 'events']
time_dst_file = 'data_with_time.csv'
event_dst_file = 'data_with_events.csv'
dynamic_match_file = 'static_dm.json'
exceptions_log = []


def write_csv(rows, dst_file):
    with open(dst_file, 'w') as f:
        f_csv = csv.DictWriter(f, data_header)
        f_csv.writeheader()
        f_csv.writerows(rows)


def get_app_and_filename(filepath: str):
    app = None
    for app in apps:
        if app in filepath:
            break
    rmost = filepath.rfind('/')
    filename = filepath[rmost:]
    return app, filename


def to_format_row(data: dict):
    rows = []
    for filepath in data:
        d = dict()
        app, filename = get_app_and_filename(filepath)
        d['app'] = app
        d['filename'] = filename
        d.update(data[filepath])
        rows.append(d)
    return rows


def iterator_log(dataset):
    for app in apps:
        d = os.path.join(dataset, app)
        for filename in os.listdir(d):
            if filename.endswith('.log'):
                filepath = os.path.join(d, filename)
                test_item = filepath[:-7]
                log = open(filepath).read().strip().split('\n')
                yield test_item, log


def iterator_test(dataset):
    for app in apps:
        d = os.path.join(dataset, app)
        for filename in os.listdir(d):
            if filename.endswith('.py') and (filename.startswith('test_') or filename.startswith('Itest')):
                filepath = os.path.join(d, filename)
                test_item = filepath[:-3]
                test = open(filepath).read().strip().split('\n')
                yield test_item, test


def get_time(line):
    m = TIME.match(line)
    time = None
    if m:
        time = format_time(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return time


def calculate_time(log):
    start_time = get_time(log[0])
    end_time = get_time(log[-1])
    time = -1
    if start_time and end_time:
        if start_time.day == end_time.day:
            if end_time.hour == start_time.hour:
                time = end_time.minute - start_time.minute
            else:
                if end_time.hour - start_time.hour < 2:
                    time = (end_time.hour - start_time.hour) * 60 + end_time.minute - start_time.minute

    return time


def analysis_time(dataset):
    result = dict()
    for item, log in iterator_log(dataset):
        time = calculate_time(log)
        if time == -1:
            exceptions_log.append(item)
        result[item] = {'time': time}
    print('\n'.join(exceptions_log))
    return result


def get_events(test: list):
    ntest = []
    i = 4
    while i != len(test):
        if 'com.google.android.inputmethod.latin' in test[i]:
            i += 2
            continue
        if 'd.sleep(3)' in test[i]:
            i += 1
            continue
        ntest.append(test[i])
        i += 1
    return ntest


def analysis_events(dataset):
    result = dict()
    for item, test in iterator_test(dataset):
        events = get_events(test)
        if len(events) == 0:
            exceptions_log.append(item)
        result[item] = {'events': len(events)}
    print('\n'.join(exceptions_log))
    return result


def iterator_dynamic_match(log):
    screenshots = []
    match_widgets = []
    descriptions = []
    for line in log:
        screenshot = SCREENSHOT.findall(line)
        description = DESCRIPTION.findall(line)
        if len(screenshot) != 0:
            screenshots += screenshot
        if len(description) != 0:
            descriptions += description
        if 'executor - INFO - match widget' in line:
            offset = len('match widget')
            index = line.find('match widget')
            match_widgets.append(line[index + offset + 1:])
    return screenshots, match_widgets, descriptions


def analysis_screenshot(dataset):
    total = dict()
    for filepath, log in iterator_log(dataset):
        screenshots, match_widgets, description = iterator_dynamic_match(log)
        if len(screenshots) != len(match_widgets):
            exceptions_log.append(filepath)
        else:
            s_ms = []
            for s, m, d in zip(screenshots, match_widgets, description):
                s_m = dict()
                s_m['screenshot'] = s
                s_m['match_widget'] = m
                s_m['description'] = d
                s_ms.append(s_m)
            total[filepath] = s_ms

    json.dump(total, open(dynamic_match_file, 'w'), indent=4)


def get_screen_folder(log_filepath):
    rmost = log_filepath.rfind('/')
    parent = log_filepath[:rmost]
    screen_folder = os.path.join(parent, 'screenshots')
    return screen_folder


def show_image(filename):
    img = Image.open(filename)
    img.show()
    img.close()


def parser_input(clazz):
    d = {'y': True, 'n': False, 'e': 'Error Screen'}
    return d[clazz]


def manual_mark_dm():
    dm = json.load(open(dynamic_match_file, 'r'))
    count = 0
    try:
        for filepath in dm:
            screen_and_widget = dm[filepath]
            screen_folder = get_screen_folder(filepath)
            for item in screen_and_widget:
                if 'class' not in item:
                    screen_filepath = os.path.join(screen_folder, item['screenshot'])
                    try:
                        show_image(screen_filepath)
                    except PIL.UnidentifiedImageError:
                        continue
                    print(
                        f'\n{filepath}\n{bcolors.OKBLUE}widget: {item["match_widget"]}{bcolors.ENDC} {bcolors.OKGREEN}description: {item["description"]}{bcolors.ENDC}')
                    clazz = input('input class[y/n/e/q]  ')
                    if clazz == 'q':
                        json.dump(dm, open(dynamic_match_file, 'w'), indent=4)
                        print(f'{count} / {len(dm)}')
                        exit(1)
                    clazz = parser_input(clazz)
                    item['class'] = clazz
            count += 1
    except Exception:
        json.dump(dm, open(dynamic_match_file, 'w'), indent=4)
        print(f'{count} / {len(dm)}')
        exit(1)


def read_csv(filename):
    from collections import namedtuple
    with open(filename) as f:
        f_csv = csv.reader(f)
        headings = next(f_csv)
        Row = namedtuple('Row', headings)
        for r in f_csv:
            yield Row(*r)


if __name__ == '__main__':
    time_result = analysis_time(ablation)
    # rows = to_format_row(result)
    # write_csv(rows, time_dst_file)
    event_result = analysis_events(ablation)
    result = {}
    for file in time_result.keys():
        time = time_result[file]
        event = event_result[file]
        r = {}
        r.update(time)
        r.update(event)
        result[file] = r
    rows = to_format_row(result)
    write_csv(rows, 'ablation_record.csv')
    # manual_mark_dm()
    # dm = json.load(open(dynamic_match_file))
    # T = 0
    # F = 0
    # E = 0
    # for file in dm:
    #     for swd in dm[file]:
    #         if type(swd['class']) == bool:
    #             if swd['class']:
    #                 T += 1
    #             else:
    #                 F += 1
    #         else:
    #             E += 1
    # total = T + F + E
    # print(total)
    # print(T/total, F/total, E/total)
    #
