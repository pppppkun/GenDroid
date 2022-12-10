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


import ast
import astpretty
import astor
from ast import *


class InsertDump(ast.NodeTransformer):
    def __init__(self):
        # self.insert_line = ast.Expr(ast.Call(
        #     func=ast.Attribute(
        #         value=ast.Name(id='d', ctx=ast.Load()),
        #         attr='dump_hierarchy',
        #         ctx=ast.Load()
        #     ),
        #     args=[],
        #     keywords=[]
        # ))
        self.insert_line = ast.parse('d.dump_hierarchy()').body[0]

    def visit_Call(self, node: Call):
        if hasattr(node.func, 'value'):
            d = node.func.value.__dict__
            if 'keywords' in d:
                return True

    def visit_Expr(self, node: Expr):
        if isinstance(node.value, ast.Call):
            return self.visit_Call(node.value)
        return None

    def generic_visit(self, node: AST):
        body = []
        for line in getattr(node, 'body', []):
            if isinstance(line, ast.Expr):
                if self.visit_Expr(line):
                    body.append(self.insert_line)
            body.append(line)
        node.body = body
        return node


def hack_script():
    path = '/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/chrome/dynamic/test_chrome20.py'
    source = open(path, 'r').read()
    source = ast.parse(source)
    hack_source = InsertDump().visit(source)
    hack_source = ast.fix_missing_locations(hack_source)
    source = astor.to_source(hack_source)
    print(source)


def static():
    # predict_w = json.load(open('predict_widget_rich.json'))
    # origin = '/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/origin_step_with_position.csv'
    # f = open(origin, 'r')
    # f = csv.DictReader(f)
    # i = 0
    # new_predict_w = {}
    # for row in f:
    #     if row['script'] == 'cant':
    #         predict_w[str(i)]['reason'] = row['reason']
    #     if row['script'] == 'duplicated':
    #         predict_w[str(i)]['reason'] = 'duplicated'
    #     i += 1
    # # print(predict_w)
    # json.dump(predict_w, open('predict_widget_rich.json', 'w'), indent=4)
    predict_w = json.load(open('predict_widget_rich.json'))
    # apps = ['setting', 'gmail', 'photo', 'clock', 'contact', 'google', 'chrome']
    apps = ['photo']
    for app in apps:
        total = 0
        count = 0
        i = 0
        for k in predict_w:
            content = predict_w[k]
            if content['app'] == app:
                if 'reason' not in content or (content['reason'] == 'Lack'):
                    # if 'reason' in content and content['reason'] != 'duplicated' and content['reason'] != 'UI':
                    # print(int(k) + 2)
                    count += content['block']
                    i += 1
                    total += len(content['predict'])
                    print(content)
                    input()
            #     if 'block' not in content:
            #         print(k)
            #         print(content['predict'])
            #         print(content['app'])
            #         print(content['description'])
            #         if 'reason' in content:
            #             print(content['reason'])
            #         s = input()
            #         if s == 'q':
            #             break
            #         block = int(s)
            #         content['block'] = block
            # json.dump(predict_w, open('predict_widget_rich.json', 'w'), indent=4)
            # print(total, count, i)
        print(f'{app} script:{i} descriptions:{total} coverage:{count}')
        # print(count / total)


def check():
    origin = '/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/origin_step_with_position.csv'
    f = open(origin)
    f = csv.DictReader(f)
    postprocess_data = '/users/pkun/pycharmprojects/ui_api_automated_test/decision_data/data_without_action_ui.json'
    d = json.load(open(postprocess_data))
    i = 0
    for row in f:
        if row['script'] == 'duplicated':
            print(i, row)
        i += 1


if __name__ == '__main__':
    check()
