"""
this class need to record some information when execute something such as start a activity or system related config
change
"""
import json
import time
from pyecharts import options as opts
from pyecharts.charts import Tree
from demo.event import event_init_map, KEY_EVENTS


class Record:
    def __init__(self, data):
        for i in data:
            self.__setattr__(i, data[i])
        if self.action not in KEY_EVENTS and 'selector' not in data:
            self.event = None
        else:
            self.event = event_init_map[self.action](self)

    def __str__(self):
        return 'Record: action={action}, description={description}'.format(action=self.action,
                                                                           description=self.description)


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
        action,
        file_path,
        device,
        description,
        given=None,
        when=None,
        then=None,
        xml=None,
        event_series=None,
        depend=None,
        action_data=None,
        screen_shot_path=None,
        selector=None,
):
    file_content = json.load(open(file_path, 'r'))
    record = dict()
    record['action'] = action
    if selector:
        record['selector'] = selector
    if screen_shot_path and device:
        device.screenshot(screen_shot_path)
        record['screen_shot_path'] = screen_shot_path
    if screen_shot_path and not device:
        raise RuntimeError('not specify device')
    record['current_info'] = device.app_current()
    record['time'] = time.time()
    record['description'] = description
    if given:
        record['given'] = given
    if when:
        record['when'] = when
    if then:
        record['then'] = then
    record['event_series'] = event_series
    record['depend'] = depend
    record['xml'] = xml
    if action_data:
        record['action_data'] = action_data
    file_content['record_list'].append(record)
    json.dump(file_content, open(file_path, 'w'))


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
    record_visualization('../../benchmark/simpleCalendarPro/result.json')
