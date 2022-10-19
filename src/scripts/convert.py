import enum
import json
import os
import random
import re
from functools import reduce
import csv
from collections import namedtuple
from xml.etree import ElementTree as et
import nltk
import numpy as np
from nltk.corpus import stopwords
from gendroid.confidence import get_most_important_attribute, predict_use_sbert
import spacy

nlp = spacy.load('en_core_web_trf')

direction = [
    'top', 'bottom', 'upper', 'left', 'right'
]

location_words = direction + ['corner']

relative = [
    'under', 'above', 'below',
]

absolute = [
    'at', 'on', 'in'
]


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
    Row = namedtuple('Row', ['id', 'description', 'steps.txt', 'category', 'script', 'reason'])
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


class LocationType(enum.Enum):
    NULL_LOCATION = 0
    ABSOLUTE = 1
    RELATIVE = 2


class GridLocation(enum.Enum):
    TOP_LEFT = 0
    TOP_CENTER = 1
    TOP_RIGHT = 2
    LEFT = 3
    CENTER = 4
    RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_CENTER = 7
    BOTTOM_RIGHT = 8


class Location:
    up = ['up', 'upper', 'top']

    left = ['left']

    right = ['right']

    down = ['bottom', 'under']

    center = ['center', 'near']

    map_ = {
        **{u: 1 for u in up},
        **{l: -1 for l in left},
        **{r: 1 for r in right},
        **{d: 7 for d in down},
        **{c: 4 for c in center}
    }

    def __init__(self, location_type, info):
        self.location_type = location_type
        self.info = info
        self.grid = None
        self.relative = None
        self.neighbor = None
        self.analysis()

    def analysis(self):
        self.grid = 0
        if self.location_type == LocationType.NULL_LOCATION:
            self.info = 'None location info'
        if self.location_type == LocationType.RELATIVE:
            self.info = nltk.word_tokenize(self.info)
            location = []
            for w in relative + direction:
                if w in self.info:
                    location.append(w)
                    self.info.remove(w)
            self.info = [word for word in self.info if word not in stopwords.words('english')]
            self.neighbor = ' '.join(self.info)
            for i in location:
                for key in Location.map_:
                    if i == key:
                        self.grid += Location.map_[key]
            self.relative = self.grid
        if self.location_type == LocationType.ABSOLUTE:
            location = nltk.word_tokenize(self.info)
            location = [word for word in location if word not in stopwords.words('english')]
            if 'corner' in location:
                location.remove('corner')
            for i in location:
                for key in Location.map_:
                    if i == key:
                        self.grid += Location.map_[key]
            self.grid = GridLocation(self.grid)
            self.info = ' '.join(location)

    def calculate_grid(self):
        pass

    def grid_index(self):
        if self.location_type == LocationType.ABSOLUTE:
            return self.grid.value
        if self.location_type == LocationType.RELATIVE:
            return self.grid + 10

    def __str__(self):
        if self.location_type == LocationType.NULL_LOCATION:
            return 'None Location Info'
        if self.location_type == LocationType.ABSOLUTE:
            return self.info + ' ' + self.grid.__str__()
        if self.location_type == LocationType.RELATIVE:
            return str(self.relative) + ' ' + self.neighbor


def recognize_location_type(words):
    location_type = LocationType.NULL_LOCATION
    for i in relative:
        if i in words:
            location_type = LocationType.RELATIVE
            return location_type
    for i in absolute:
        if i in words:
            if 'of' in words:
                location_type = LocationType.RELATIVE
            else:
                for j in location_words:
                    if j in words:
                        location_type = LocationType.ABSOLUTE
                return location_type
    return location_type


def event_and_positive_analysis(words):
    doc = nlp(' '.join(words))
    action_word = []
    location_word = []
    for i in range(len(doc)):
        if doc[i].pos_ == 'VERB':
            action_word.append(i)
        if doc[i].pos_ == 'ADP':
            location_word.append(i)
    if len(action_word) == 0:
        if 'tap' in words:
            action_word = [words.index('tap')]
    action_index = action_word[0]
    if len(location_word) > 1:
        for index in location_word:
            if abs(action_index - index) <= 2:
                location_word.remove(index)
    location_index = location_word[0]
    if action_index < location_index:
        location = doc[location_index:]
        event = doc[:location_index]
    else:
        location = doc[:action_index]
        event = doc[action_index:]
    return event.text, location.text


def analysis_description(sentence):
    # origin = '/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/origin_step_with_position.csv'
    # nlp = spacy.load("en_core_web_trf")
    # f = open(origin)
    # f = csv.DictReader(f)
    # for row in f:
    # sentences = row['steps']
    # if 'yes' != row['script']:
    #     continue
    # if '@' in sentences:
    #     continue
    # sentences = sentences.split('.')
    # sentences = filter(lambda x: len(x) != 0, map(lambda x: x.strip(), sentences))
    # sentences = list(sentences)
    # for sent in sentences:
    words = nltk.word_tokenize(sentence)
    flag = False
    if 'back' in words and words[words.index('back') + 1] == 'up':
        words[words.index('back')] = 'backup'
        words.pop(words.index('backup') + 1)
        flag = True
    location_type = recognize_location_type(words)
    location = None
    if location_type != LocationType.NULL_LOCATION:
        try:
            event, location = event_and_positive_analysis(words)
        except BaseException:
            return None, None
        event = nltk.word_tokenize(event)
    else:
        event = words
    # event = stopwords.words('english')
    event = list(filter(lambda x: x == 'more' or x not in stopwords.words('english'), event))
    if flag:
        index = event.index('backup')
        event.insert(index + 1, 'up')
        event[index] = 'back'
    action = event[0]
    ui_info = ' '.join(event[1:])
    location = Location(location_type, location)
    # print((action, ui_info, location.__str__()))
    return action, ui_info


def add_action_and_ui_info():
    d = json.load(open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data.json'))
    for i in d:
        steps = d[i]
        for step in steps:
            action, ui_info = analysis_description(step)
            if action is None and ui_info is None:
                print(i)
            else:
                steps[step]['action'] = action
                steps[step]['ui_info'] = ui_info
    json.dump(d, open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data_with_action_ui.json', 'w'),
              indent=4)


resource_id_pattern = re.compile(r'.*:id/(.*)')


def process_resource_id(x): return resource_id_pattern.match(x).group(1).replace('/', ' ').replace('_',
                                                                                                   ' ')


def pos_analysis(description):
    doc = nlp(description)
    actions = []
    for token in doc:
        if token.pos_ == 'VERB':
            actions.append(token)
    ui_infos = []
    for action in actions:
        ui_info = [child for child in action.children]
        if len(ui_info) == 0:
            # ui_infos.append('')
            pass
        else:
            ui_info = ui_info[0]
            ui_info = ' '.join([child.text for child in ui_info.subtree])
            ui_infos.append(ui_info)
    if len(ui_infos) == 0:
        ui_infos.append(description)
    actions = list(map(lambda x: x.text, actions))
    return actions, ui_infos


def add_similarity():
    d = json.load(open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data_with_action_ui.json'))
    attrs = ['text', 'description', 'resourceId']
    widgets = ['true widget', 'false widget']
    for index in d:
        descriptions = d[index]
        for desc in descriptions:
            data = descriptions[desc]
            action = data['action']
            ui_info = data['ui_info']
            # widget = data['true widget']
            for w in widgets:
                widget = data[w]
                if 'result' in widget:
                    continue
                attribute = ''
                for key in attrs:
                    if widget[key] != '':
                        attribute = widget[key]
                        break
                if key == 'resourceId':
                    attribute = process_resource_id(attribute)
                attr_actions, attr_ui_infos = pos_analysis(attribute)
                scores = []
                for attr_action in attr_actions:
                    scores.append(predict_use_sbert(attr_action, action))
                for attr_ui_info in attr_ui_infos:
                    scores.append(predict_use_sbert(attr_ui_info, ui_info))
                scores.append(predict_use_sbert(attribute, action + ' ' + ui_info))
                score = np.max(scores)
                widget['similarity'] = round(float(score), 2)

    json.dump(d, open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data_with_action_ui.json', 'w'),
              indent=4)


def generate_absolute_bounds(index):
    max_x = 1080
    max_y = 1920
    grids = [
        [max_x / 3 * (i - 1),
         max_y / 3 * (j - 1),
         max_x / 3 * i,
         max_y / 3 * j,
         ] for j in range(1, 4) for i in range(1, 4)
    ]
    grid = grids[index]
    x1, y1, x2, y2 = grid
    nx1, ny1 = random.randint(x1, x2), random.randint(y1, y2)
    nx2, ny2 = random.randint(nx1, x2), random.randint(ny1, y2)
    return [nx1, ny1, nx2, ny2]


def generate_relative_bounds(index, relative_bounds):
    return relative_bounds


def get_grid_random_except_param(grid):
    new_grid = grid
    while new_grid == grid:
        new_grid = random.randint(0, 8)
    return new_grid


def add_false_sample():
    d = json.load(open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data_with_action_ui.json'))
    for index in d:
        descriptions = d[index]
        for desc in descriptions:
            data = descriptions[desc]
            location_type = data['location type']
            false_widget = data['false widget']
            true_widget = data['true widget']
            x1, y1, x2, y2 = true_widget['bounds']
            bounds = [x1, y1, x2, y2]
            if 'result' not in false_widget:
                continue
            false_widget.pop('result')
            if location_type == 'null':
                # same position but different similarity
                false_widget['similarity'] = random.uniform(0, true_widget['similarity'])
                new_bounds = []
                for i in bounds:
                    i += random.randint(0, 50)
                    new_bounds.append(i)
                false_widget['bounds'] = new_bounds
                continue
            if true_widget['similarity'] > 0.9:
                false_widget['similarity'] = true_widget['similarity'] + random.uniform(-0.2, -0.1)
            else:
                false_widget['similarity'] = true_widget['similarity'] + random.uniform(-0.1, 0.1)
            if location_type == 'absolute':
                # different position but same similarity
                location = Location(LocationType.ABSOLUTE, data['absolute'])
                data['grid int'] = location.grid.value
                false_widget['bounds'] = generate_absolute_bounds(get_grid_random_except_param(location.grid.value))
            if location_type == 'relative':
                # different position but same similarity
                relative_widget = data['relative widget']
                location = Location(LocationType.RELATIVE, data['relative'])
                data['relative int'] = location.grid
                false_widget['bounds'] = generate_relative_bounds(get_grid_random_except_param(location.grid.value),
                                                                  relative_widget['bounds'])


def check_confidence():
    d = json.load(open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data_with_action_ui.json'))
    for index in d:
        descriptions = d[index]
        for desc in descriptions:
            data = descriptions[desc]
            confidence = data['true widget']['similarity']
            if confidence < 0.5:
                print(index, desc)


if __name__ == '__main__':
    # analysis_position()
    # create_decision_data()
    # add_decision_data()
    # print(analysis_position('click backup'))
    # add_similarity()
    add_false_sample()
    # check_confidence()
