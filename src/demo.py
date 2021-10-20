import json
import xml.etree.ElementTree as et
import xml.dom.minidom as md

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


def find_match_node_with_selector(selector, xml):
    nodes = get_all_nodes(xml)
    keys = selector.keys()
    attr = ['rid', 'text', 'contains', 'class']
    trans = {
        'rid': 'resource-id',
        'text': 'text',
        'contains': 'text',
        'class': 'classIndex',
        'instance': 'idIndex'
    }
    for node in nodes:
        pass

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
    result_json = open(path)
    data = json.loads(result_json.read())['case_data']
    for test_action in data:
        if 'selector' in test_action:
            selector = test_action['selector']
            xml = test_action['xml']
            break
    root = et.fromstring(xml)
    nodes = []
    get_all_nodes(root, nodes)
    keys = selector.keys()
    print(len(keys))
