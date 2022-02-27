"""
this class need to record some information when execute something such as start a activity or system related config
change
"""
import json
import time
from pyecharts import options as opts
from pyecharts.charts import Tree
from demo.event import event_init_map


class Record:
    def __init__(self, data):
        self.action = None
        self.event = None
        self.selector = None
        self.action_data = None
        self.description = None
        for i in data:
            self.__setattr__(i, data[i])
        if self.action:
            self.event = event_init_map[self.action](self)

    def __str__(self):
        return 'Record: action={action}, description={description}'.format(action=self.action,
                                                                           description=self.description)


def create_record():
    records = {'d2e': []}
    f = open('record.json', 'w')
    json.dump(records, f)
    f.close()


def record_events(
        description,
        event_series,
        widgets,
        pre_device_info,
        post_device_info,
        pre_screenshot,
        post_screenshot
):
    d = dict()
    d['description'] = description
    d['event_series'] = event_series
    d['widgets'] = widgets
    d['pre_device_info'] = pre_device_info
    d['post_device_info'] = post_device_info
    d['pre_screenshot'] = pre_screenshot
    d['post_screenshot'] = post_screenshot

    f = open('record.json', 'r')
    records = json.load(f)
    f.close()
    records['d2e'].append(d)
    f = open('record.json', 'w')
    json.dump(records, f)
    f.close()


def create_tree(record_content):
    record_list = record_content['record_list']
    root = record_content['description']
    node = dict()
    for record in record_list:
        leaf = record['action']
        leaf_father = record['event_series']
        leaf_father_father = record['depend']
        leaf_father_node = node.setdefault(leaf_father, {'name': leaf_father, 'children': []})
        leaf_father_node['children'].append({'name': leaf})
        leaf_father_father_node = node.setdefault(leaf_father_father, {'name': leaf_father_father, 'children': []})
        if leaf_father_node not in leaf_father_father_node['children']:
            leaf_father_father_node['children'].append(leaf_father_node)
    # print(json.dumps(node[root], indent=4))
    return node[root]


def record_visualization(record_path):
    record_content = json.load(open(record_path, 'r'))
    tree = create_tree(record_content)
    (
        Tree()
            .add(
            "",
            [tree],
            collapse_interval=4,
            orient="TB",
            label_opts=opts.LabelOpts(
                position="top",
                horizontal_align="right",
                vertical_align="middle",
            ),
        )
            .set_global_opts(title_opts=opts.TitleOpts(title='add task'))
            .set_series_opts(label_opts=opts.LabelOpts(font_size=16))
            .render("tree_top_bottom.html")
    )


if __name__ == '__main__':
    record = Record(
        {'description': 'fill the event title'})
