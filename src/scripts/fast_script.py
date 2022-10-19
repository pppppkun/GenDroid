import csv
import json


def create_decision_data():
    origin = '/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/origin_step_with_position.csv'
    f = open(origin)
    f = csv.DictReader(f)
    d = {}
    i = 0
    for row in f:
        i += 1
        sentences = row['steps']
        if row['script'] != 'yes':
            sentences = sentences.split('.')
            sentences = filter(lambda x: len(x) != 0, map(lambda x: x.strip(), sentences))
            sentences = list(sentences)
            d[i] = {}
            for sent in sentences:
                d[i][sent] = {
                    'app': row['category'],
                    'true widget': {},
                    'false widget': {}
                }
    json.dump(d,
              open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data_without_action_ui.json', 'w'),
              indent=4)


def add_index():
    origin = '/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/origin_step_with_position.csv'
    d = json.load(open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data.json'))
    nd = {}
    f = csv.DictReader(open(origin))
    i = 0
    for row in f:
        i += 1
        sentences = row['steps']
        if row['script'] != 'yes':
            sentences = sentences.split('.')
            sentences = filter(lambda x: len(x) != 0, map(lambda x: x.strip(), sentences))
            sentences = list(sentences)
            nd[i] = {}
            for sent in sentences:
                if sent in d:
                    nd[i][sent] = d[sent]
                    if 'id' in nd[i][sent]:
                        nd[i][sent].pop('id')
    json.dump(nd, open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data.json', 'w'), indent=4)


def add_decision_data():
    d = json.load(open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data.json'))
    i = 1
    for sent in d:
        i += 1
        if 'location type' in d[sent]:
            continue
        print(f'{i * 100 / len(d):.0f}% ' + sent)
        location_type = input()
        if location_type == 'exit':
            break
        location_type = int(location_type)
        if location_type == 0:
            location_type = 'null'
        if location_type == 1:
            location_type = 'relative'
        if location_type == 2:
            location_type = 'absolute'
        d[sent]['location type'] = location_type
        if location_type == 'absolute':
            d[sent]['absolute'] = input()
        if location_type == 'relative':
            d[sent]['relative widget'] = {}
            d[sent]['relative'] = input()
    json.dump(d, open('/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data.json', 'w'), indent=4)

