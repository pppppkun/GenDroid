import json
from os import remove
import xml.etree.ElementTree as et
import xml.dom.minidom as md

PREP = 'prep'
INDEX = 'index'
OP = 'op'
INSTANCE = 'instance'

selector_attrs = ['rid', 'text', 'contains', 'class']
transfer = {
    'rid': {PREP: 'resource-id', INDEX: 'idIndex', OP: lambda x, y: x == y},
    'text': {PREP: 'text', INDEX: 'textIndex', OP: lambda x, y: x == y},
    'contains': {PREP: 'text', INDEX: 'textIndex', OP: lambda x, y: x in y},
    'class': {PREP: 'class', INDEX: 'classIndex', OP: lambda x, y: x == y},
    'description': {PREP: 'content-desc', INDEX: None, OP: lambda x, y: x == y}
}

path = '/Users/pkun/PycharmProjects/ui_api_automated_test/testlog_oldVersion-base118/36663/1614759354_result_test_1receipts_214257.json'


def json_file_process():
    result_json = open(path)
    data = json.loads(result_json.read())['case_data']
    for test_action in data:
        if 'selector' in test_action:
            case_data_process(data)


def get_all_nodes(root, ns: list):
    for child in root:
        ns.append(child)
        get_all_nodes(child, ns)


def remove_and_return(nodes, node):
    nodes.remove(node)
    return node, nodes


def find_match_node_with_selector(selector, xml):
    nodes = get_all_nodes(xml)
    keys = selector.keys()
    for node in nodes:
        if len(keys) > 2:
           if INSTANCE in keys:
               if 'rid' in keys and 'text' in keys:
                   if selector['rid'] == u'com.tencent.mm:id/set_pay_pwd_confirm':
                       if selector['rid'] == node['resource-id'] and selector['instance'] == node['idIndex']:
                           return remove_and_return(nodes, node)
        if len(keys) == 2:
            for attr in selector_attrs:
                if attr in keys and transfer[attr][OP](selector[attr], node[transfer[attr][PREP]]):
                    if INSTANCE not in keys:
                        return remove_and_return(nodes, node)
                    else:
                        if selector[INSTANCE] == node[transfer[attr][INDEX]]:
                            return remove_and_return(nodes, node)
        if len(keys) == 1:
            selector_attrs_ = selector_attrs + ['description']
            for attr in selector_attrs_:
                if attr in keys and transfer[attr][OP](selector[attr], node[transfer[attr][PREP]]):
                    return remove_and_return(nodes, node)


def get_doc_by_node(matched_node, is_negative):
    if matched_node['text'] != '':
        return matched_node['text']
    if matched_node['content-desc']!='':
        return matched_node['content-desc']
    if matched_node['resource-id']!='' and not is_negative:
        return matched_node['resource-id']
    if matched_node['class']!='' and not is_negative:
        return matched_node['class']
    return None 
        

def case_data_process(data):
    selector, xml = None, None
    selectors = []

    for _ in selectors:
        print(_)

    for test_action in data:
        if 'selector' in test_action:
            selector = test_action['selector']
            xml = test_action['xml']
            break

    root = et.fromstring(xml)
    print(selector.keys())
    if 'text' in selector.keys():
        print(1)
    for child in root:
        print(child.tag, child.attrib)
    nodes = set()
    keys = selector.keys()

    care_keys = ['instance', 'rid', 'text', 'class', 'description', 'contains']


if __name__ == '__main__':
    # result_json = open(path)
    # data = json.loads(result_json.read())['case_data']
    # for test_action in data:
    #     if 'selector' in test_action:
    #         selector = test_action['selector']
    #         xml = test_action['xml']
    #         break
    # root = et.fromstring(xml)
    # nodes = []
    # get_all_nodes(root, nodes)
    # keys = selector.keys()
    # print(len(keys))
    a = {
        'a': lambda x, y: x == y,
        'b': lambda x, y: x in y
    }
    val1 = a['a'](1, 1)
    val2 = a['a'](1, 2)
    val3 = a['b'](2, [1, 2, 3])
    val4 = a['b'](2, [3, 4, 5])
    print(val1, val2, val3, val4)
    if a['b'](2, [1, 2, 3]):
        print(1)
