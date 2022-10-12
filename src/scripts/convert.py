import json
import os
from functools import reduce
import csv
from collections import namedtuple
from xml.etree import ElementTree as et


# from gendroid.confidence import postprocess_keys, get_attribute_base_on_class


def bounds2list(bounds):
    s = bounds
    s = '[' + s + ']'
    s = s[:s.find(']') + 1] + ',' + s[s.find(']') + 1:]
    return eval(s)


def gui_xml2json_helper(node):
    children = []
    d_ = node.attrib
    for child in node:
        children.append(gui_xml2json_helper(child))
    d_['children'] = children
    if 'bounds' not in d_:
        d_['bounds'] = None
    else:
        bounds = bounds2list(d_['bounds'])
        d_['bounds'] = [
            bounds[0][0],
            bounds[1][0],
            bounds[0][1],
            bounds[1][1]
        ]
    return d_


def gui_xml2json(xml: et, activity_name):
    root = et.fromstring(xml)
    d = gui_xml2json_helper(root)
    result = {
        'activity_name': activity_name,
        'is_keyboard_deployed': False, 'activity': {'root': d}}
    # f = open('calendar.json', 'w+')
    # json.dump(result, f, indent=4)
    return result


# def trace2dataset(trace_file):
#     traces = json.load(trace_file)
#     total_description = traces['description']
#     atomic_description_and_widget = []
#     for trace in traces['trace']:
#         atomic_description = trace['description']
#         widget = trace['widget']
#         keys = get_attribute_base_on_class(widget)
#         keys = postprocess_keys(keys)
#         widget_semantic = keys
#         atomic_description_and_widget.append([atomic_description, widget])


def helper(file_path):
    import csv
    from collections import namedtuple
    rows = []
    with open(file_path) as f:
        f_csv = csv.reader(f)
        headings = next(f_csv)
        Row = namedtuple('Row', headings)
        for r in f_csv:
            row = Row(*r)
            rows.append(row)
            # Process row
    return rows


def fetch_origin_script(direction):
    scripts = filter(lambda x: x.endswith('.py'), os.listdir(direction))
    scripts = filter(lambda x: x != 'runner.py', scripts)
    scripts = filter(lambda x: not x.startswith('test_') and not x.startswith('_test'), scripts)
    scripts = list(scripts)
    return scripts


def delete_evaluate_data():
    direction = '/Users/pkun/PycharmProjects/ui_api_automated_test/ablation'
    apps = os.listdir(direction)
    apps = filter(lambda x: os.path.isdir(os.path.join(direction, x)), apps)
    files = map(lambda x: (x, os.listdir(os.path.join(direction, x))), apps)
    for app, need_to_remove in files:
        need_to_remove = filter(
            lambda f: f.startswith('test_') or f.startswith('Itest_') or f == 'screenshots' or f.startswith('_test'),
            need_to_remove)
        for file in need_to_remove:
            os.system(f'rm -r {os.path.join(direction, app, file)}')


def make_runner():
    direction = '/Users/pkun/PycharmProjects/ui_api_automated_test/ablation'
    runner_format = 'import subprocess\nimport os\nfilepaths= [\n    {filepaths}\n]\nfor filepath in filepaths:\n    subprocess.call(["python3", filepath])'
    apps = os.listdir(direction)
    apps = filter(lambda x: os.path.isdir(os.path.join(direction, x)), apps)
    scripts_tuple = map(lambda x: (x, fetch_origin_script(os.path.join(direction, x))), apps)
    for app, scripts in scripts_tuple:
        filepaths = []
        for script in scripts:
            filepaths.append(script)
        filepaths = ',\n    '.join([repr(filepath) for filepath in filepaths])
        runner = runner_format.format(filepaths=filepaths)
        target = os.path.join(direction, app, 'runner.py')
        f = open(target, 'w+')
        f.write(runner)


def write_csv(data_header, rows, dst_file):
    with open(dst_file, 'w') as f:
        f_csv = csv.DictWriter(f, data_header)
        f_csv.writeheader()
        f_csv.writerows(rows)


def recovery_pixel_help():
    processed = '/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/processed.csv'
    origin = '/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/origin_step.txt'
    count = 0
    checkpoint = 0
    origin = open(origin).read().split('\n')
    new_rows = []
    Row = namedtuple('Row', ['id', 'description', 'steps', 'category', 'script', 'reason'])
    f = open(processed)
    f_csv = csv.reader(f)
    headings = next(f_csv)
    for r in f_csv:
        if count < checkpoint:
            count += 1
            continue
        row = Row(*r)
        if row.script == 'yes':
            print(count)
            print(origin[count])
            print(row.steps)
            before = input()
            if before == 'exit':
                break
            new_steps = before + row.steps
            new_row = Row(id=row.id, description=row.description, steps=new_steps, script=row.script,
                          reason=row.reason, category=row.category)
            new_rows.append(new_row._asdict())
        else:
            new_rows.append(row._asdict())
        count += 1
    print(checkpoint)
    write_csv(headings, new_rows, 'recovery.csv')


if __name__ == '__main__':
    pass