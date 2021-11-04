import json
import os
import xml.etree.ElementTree as et
import xml.dom.minidom as md
import numpy as np


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


def json_file_process(path, is_train_set):
    res = []
    result_json = open(path)
    data = json.loads(result_json.read())['case_data']
    for test_action in data:
        if 'selector' in test_action:
            ret = test_action_process(test_action, is_train_set)
            if ret is not None:
                res.append(ret)
    return res

def test_action_process(test_action, is_train_set):
    try:
        matched_node, other_nodes = find_match_node_with_selector(test_action['selector'], et.fromstring(test_action['xml']))
    except RuntimeError:
        return 
    index = -6 if is_train_set else -2
    ret = get_positive_and_negative_example(test_action['trace'], matched_node, other_nodes, test_action['xml'], -6)
    return ret

def get_all_nodes(root, ns: list):
    for child in root:
        ns.append(child)
        get_all_nodes(child, ns)


def remove_and_return(nodes, node):
    nodes.remove(node)
    return node, nodes

def get_all_nodes_key(ns):
    ret = []
    for i in ns:
        ret.append(i.attrib)
    return ret

def find_match_node_with_selector(selector, xml):
    nodes = []
    get_all_nodes(xml, nodes)
    nodes = get_all_nodes_key(nodes)
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
                        try:
                            if selector[INSTANCE] == node[transfer[attr][INDEX]]:
                                return remove_and_return(nodes, node)
                        except KeyError:
                            # print(selector, node)
                            pass
        if len(keys) == 1:
            selector_attrs_ = selector_attrs + ['description']
            for attr in selector_attrs_:
                if attr in keys and transfer[attr][OP](selector[attr], node[transfer[attr][PREP]]):
                    return remove_and_return(nodes, node)
    raise RuntimeError('cannot match')

def get_positive_and_negative_example(trace, matched_node, other_nodes, xml, trace_index):
    positive_doc = get_doc_by_node(matched_node, is_negative=False).replace('\t',' ')

    query = trace.split('\n')[trace_index].split(" ")[0].replace('_',' ')

    negative_docs = []
    for node in other_nodes:
        negative_doc = get_doc_by_node(node, is_negative=True)
        if not negative_doc is None:
            negative_docs.append(negative_doc.replace('\t', " ").replace("\n", " "))
    ret = {
        'query': query.replace('_', ' '),
        'positive_doc': positive_doc.replace('\t', ' '),
        'negative_docs': negative_docs,
        'xml': xml
    }
    return ret

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

def see_predict():
    predict = open(os.path.join('data','predict.txt'), 'r')
    s = predict.read()
    l = s.split('\n')
    t = dict() 
    f = dict()
    ld = dict()
    index = 0
    j = 0
    while index < len(l):
        batch = l[index:index+4]
        text_a = batch[0][8:]
        text_b = batch[1][8:]
        label = batch[2][6:]
        prediction = batch[3][11:]

        index_ = prediction.find(' ')
        prediction = prediction[:index_] + ',' + prediction[index_:]
        prediction = eval(prediction)
        prediction = 'yes' if prediction[0] > prediction[1] else 'no'
        ld['text_a'] = text_a
        ld['text_b'] = text_b
        ld['label'] = label
        ld['prediction'] = prediction
        if prediction == label:
            t[j] = ld.copy()
        else:
            f[j] = ld.copy()
        j += 1
        index = index + 5
    predict_true = open(os.path.join('data', 'predict_true.json'), 'w')
    predict_false = open(os.path.join('data', 'predict_false.json'), 'w')
    predict = open(os.path.join('data', 'predict.json'), 'w')
    json.dump(t, predict_true, ensure_ascii=False)
    json.dump(f, predict_false, ensure_ascii=False)
    json.dump({**t, **f}, predict, ensure_ascii=False, sort_keys=True)

if __name__ == '__main__':
    # see_predict()
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
    # for i in nodes:
    #     print(i.attrib)
    # path = '/Users/pkun/PycharmProjects/ui_api_automated_test/testlog_oldVersion-base118/36663/1614759354_result_test_1receipts_214257.json'
    # json_file_process(path)
    # demo = open('demo.txt', 'w')
    # for train in res:
    #     if train['query'] == 'init' or train['query'] == 'login' or train['query'] == 'system requests from direct business':
    #         continue
    #     label = 'yes'
    #     doc = train['query']
    #     ans = train['positive_doc'].replace('\n','')
    #     demo.write(label + '\t' + doc + '\t' + ans)
    # demo.close()
    # print(os.system('pwd'))
    pwd = os.getcwd() + '/testlog_NewVersion-basejsapi-7-copy'
    for path, __, files in os.walk(pwd):
        for file in files:
            if file.endswith('.json') and 'result' in file:
                f = open(os.path.join(path, file), 'r')
                s = json.load(f)
                f.close()
                s = json.dumps(s, ensure_ascii=False, indent=4, sort_keys=True) 
                f = open(os.path.join(path, file), 'w')
                f.write(s)
    pass