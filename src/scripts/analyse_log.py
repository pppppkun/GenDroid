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
# apps = ['chrome', 'contact', 'gmail', 'photo', 'setting', 'clock']
apps = list(filter(lambda x: os.path.isdir(os.path.join(benchmark, x)), os.listdir(benchmark)))
apps.remove('.git')
TIME = re.compile(r'\d+-\d+-(\d+) (\d+):(\d+):(\d+)')
STATEMENT = re.compile(r'd\(.*\).*')
SCREENSHOT = re.compile(r'screenshot is (\d+.png)')
MATCH_WIDGET = re.compile(r'executor - INFO - match widget ')
DESCRIPTION = re.compile('generating event for "(.*)"')
format_time = namedtuple('format_time', ['day', 'hour', 'minute', 'second'])
# data_header = ['app', 'filename', 'time', 'events']
# data_header = ['filename', 'dynamic_time', 'hybrid_time']
time_dst_file = 'data_with_time.csv'
event_dst_file = 'data_with_events.csv'
dynamic_match_file = 'static_dm.json'
exceptions_log = []


def get_data_path(dataset, app):
    return os.path.join(benchmark, app, dataset)


def write_csv(rows, dst_file, data_header):
    with open(dst_file, 'w') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(data_header)
        f_csv.writerows(rows)


def get_app_and_filename(filepath: str):
    # app = None
    # for app in apps:
    #     if app in filepath:
    #         break
    items = filepath.split('/')
    app = items[-3]
    filename = items[-1]
    # rmost = filepath.rfind('/')
    # filename = filepath[rmost + 1:]
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
        d = get_data_path(dataset, app)
        for filename in os.listdir(d):
            if filename.endswith('.log'):
                filepath = os.path.join(d, filename)
                test_item = filepath[:-7]
                log = open(filepath).read().strip().split('\n')
                yield test_item, log


def iterator_test(dataset):
    for app in apps:
        d = get_data_path(dataset, app)
        for filename in os.listdir(d):
            if filename.endswith('.py'):
                filepath = os.path.join(d, filename)
                test_item = filepath[:-3]
                test = open(filepath).read().strip().split('\n')
                yield test_item, test


def get_time(line):
    m = TIME.match(line)
    time = None
    if m:
        time = format_time(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(int(m.group(4))))
    return time


def calculate_time(log):
    start_time = get_time(log[0])
    end_time = get_time(log[-1])
    time = -1
    if start_time and end_time:
        if start_time.day == end_time.day:
            if end_time.hour == start_time.hour:
                time = (end_time.minute - start_time.minute) * 60 + end_time.second - start_time.second
            else:
                if end_time.hour - start_time.hour < 2:
                    time = (end_time.hour - start_time.hour) * 60 + end_time.minute - start_time.minute
                    time = time * 60 + end_time.second - start_time.second

    return time


def analysis_time(dataset):
    result = dict()
    for item, log in iterator_log(dataset):
        time = calculate_time(log)
        if time == -1:
            exceptions_log.append(item)
        app, filename = get_app_and_filename(item)
        result[app + '/' + filename] = {dataset + '_time': time}
    # print('\n'.join(exceptions_log))
    return result


def get_events(test: list):
    ntest = []
    i = 4
    while i != len(test):
        if test[i].startswith('#'):
            i += 1
            continue
        if 'com.google.android.inputmethod.latin' in test[i]:
            i += 2
            continue
        if 'd.sleep(3)' in test[i]:
            i += 1
            continue
        ntest.append(test[i])
        i += 1
    return len(ntest)


def analysis_events(dataset):
    result = dict()
    for item, test in iterator_test(dataset):
        events = get_events(test)
        if events == 0:
            exceptions_log.append(item)
        app, filename = get_app_and_filename(item)
        result[app + '/' + filename] = {dataset + '_event': events}
    # print('\n'.join(exceptions_log))
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


def get_covered_description():
    rows = list(read_csv('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/data.csv'))
    d = {}
    for row in rows:
        if row.app not in d:
            d[row.app] = {}
        d[row.app]['dynamic'] = int(row.dynamic)
        d[row.app]['hybrid'] = int(row.hybrid)
    return d


def boxplot():
    d = open('data_with_time.csv')
    data = csv.DictReader(d)
    from matplotlib import pyplot as plt
    df = [[], []]
    for row in data:
        df[0].append(float(row['dynamic_time']))
        df[1].append(float(row['hybrid_time']))
    # plt.tick_params(axis='x', labelsize=8)
    # fig = plt.figure(figsize=(4, 5))
    plt.boxplot(df, showmeans=True, showfliers=False, manage_ticks=True)
    plt.show()
    # for app in df:
    #     time = df[app]


def fun():
    hybrid_time = analysis_time('hybrid')
    dynamic_time = analysis_time('dynamic')
    covered_description = get_covered_description()
    print(exceptions_log)
    d = {}
    for k in hybrid_time:
        hybrid_time[k].update(dynamic_time[k])
        # hybrid_time[k].update(hybrid_event[k])
        # hybrid_time[k].update(dynamic_event[k])
    # rows = list(map(lambda x: (x, round(hybrid_time[x]['dynamic_time'] / hybrid_time[x]['dynamic_event'], 1),
    #                            round(hybrid_time[x]['hybrid_time'] / hybrid_time[x]['hybrid_event'], 1)), hybrid_time))
    rows = list(map(lambda x: (x, hybrid_time[x]['dynamic_time'], hybrid_time[x]['hybrid_time']), hybrid_time))
    write_csv(rows, time_dst_file, ['filename', 'dynamic_time', 'hybrid_time'])
    # total = sum(rows[2])


if __name__ == '__main__':
    boxplot()
    # fun()
    # d = {}
    # for k in result1:
    #     app, _ = k.split('/')
    #     d.setdefault(app, {'sum': 0})
    #     d[app]['sum'] += result1[k]['hybrid_time']
    # d[app]['count'] += 1
    # for k in d:
    # descriptions = int(input(k))
    # print(k, d[k]['sum']/descriptions)
    # print(sum(map(lambda x: d[x]['sum'], d)))
    # for k in result1:
    #     result1[k].update(result2[k])

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
