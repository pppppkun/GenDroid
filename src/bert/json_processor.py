import json
import os
import xml.etree.ElementTree as et
from abc import abstractmethod

import pandas as pd

from utils.common import files
from utils.constant import NEW_LOG

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


# transfer(rid, resource-id, idIndex, op)


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


class JsonSearch:
    def __init__(self, path, is_train_set) -> None:
        self.path = path
        self.is_train_set = is_train_set

    def json_file_process(self):
        res = []
        result_json = open(self.path)
        data = json.loads(result_json.read())['case_data']
        for test_action in data:
            if 'selector' in test_action:
                ret = self.test_action_process(test_action)
                if ret is not None:
                    res.append(ret)
        return res

    def test_action_process(self, test_action):
        try:
            matched_node, other_nodes = self.find_match_node_with_selector(
                test_action['selector'], et.fromstring(test_action['xml']))
        except RuntimeError:
            return
        # old -2 new -6
        index = -6 if self.is_train_set else -2
        ret = self.get_positive_and_negative_example(
            test_action['trace'], matched_node, other_nodes, test_action['xml'], index)
        return ret

    @abstractmethod
    def find_match_node_with_selector(self, selector, xml):
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

    @abstractmethod
    def get_doc_by_node(self, matched_node, is_negative):
        pass

    def get_positive_and_negative_example(self, trace, matched_node, other_nodes, xml, index):
        positive_doc = self.get_doc_by_node(
            matched_node, is_negative=False).replace('\t', ' ')
        query = trace.split('\n')[index].split(" ")[0].replace('_', ' ')

        negative_docs = []
        for node in other_nodes:
            negative_doc = self.get_doc_by_node(node, is_negative=True)
            if not negative_doc is None:
                negative_docs.append(negative_doc.replace(
                    '\t', " ").replace("\n", " "))
        ret = {
            'query': query,
            'positive_doc': positive_doc,
            'negative_docs': negative_docs,
            'xml': xml
        }
        return ret


class DataSetBuild(JsonSearch):
    def __init__(self, path, is_train_set) -> None:
        super().__init__(path, is_train_set)

    def get_doc_by_node(self, matched_node, is_negative):
        if matched_node['text'] != '':
            return matched_node['text']
        if matched_node['content-desc'] != '':
            return matched_node['content-desc']
        if matched_node['resource-id'] != '' and not is_negative:
            return matched_node['resource-id']
        if matched_node['class'] != '' and not is_negative:
            return matched_node['class']
        return None


class CompareBuild(JsonSearch):
    def __init__(self, path, is_train_set) -> None:
        super().__init__(path, is_train_set)

    def get_doc_by_node(self, node, is_negative):
        res = {}
        if node['text'] != '':
            res['text'] = node['text'].replace('\t', ' ')
        if node['content-desc'] != '':
            res['content-desc'] = node['content-desc'].replace('\t', ' ')
        if node['resource-id'] != '' and not is_negative:
            res['resource-id'] = node['resource-id'].replace('\t', ' ')
        if node['class'] != '' and not is_negative:
            res['class'] = node['class'].replace('\t', ' ')
        return res

    def get_positive_and_negative_example(self, trace, matched_node, other_nodes, xml, index):
        positive_doc = self.get_doc_by_node(matched_node, is_negative=False)
        query = trace.split('\n')[index].split(" ")[0].replace('_', ' ')
        negative_docs = []
        for node in other_nodes:
            negative_doc = self.get_doc_by_node(node, is_negative=True)
            if not negative_doc is None and len(negative_doc) != 0:
                for key in negative_doc:
                    negative_doc[key] = negative_doc[key].replace('\n', ' ')
                negative_docs.append(negative_doc)
        ret = {
            'query': query,
            'positive_doc': positive_doc,
            'negative_docs': negative_docs,
        }
        return ret


def see_predict():
    predict = open(os.path.join('data', 'predict.txt'), 'r')
    s = predict.read()
    l = s.split('\n')
    t = dict()
    f = dict()
    ld = dict()
    index = 0
    j = 0
    while index < len(l):
        batch = l[index:index + 4]
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


def build_data_set(log, count=None):
    is_new_log = True if log == NEW_LOG else False
    # data_set= DataSet(is_remove_duplicate=is_remove_duplicate)
    data_set = dict()
    data_set['label'] = list()
    data_set['query'] = list()
    data_set['ui_info'] = list()
    for path in files(log):
        dsb = DataSetBuild(path, is_new_log)
        res = dsb.json_file_process()
        if count is not None:
            count -= 1
            if count == 0:
                break
        for example in res:
            query = example['query']
            if query == 'init' or query == 'system requests from direct business' or query == 'wrap do repair':
                continue
            text_b = example['positive_doc'].replace('\n', ' ')
            data_set['label'].append('yes')
            data_set['query'].append(query)
            data_set['ui_info'].append(text_b)
            # data_set.add(Data('yes', query, text_b))
            for n_c in example['negative_docs']:
                data_set['label'].append('no')
                data_set['query'].append(query)
                data_set['ui_info'].append(n_c)
                # data_set.add(Data('no', query, n_c))
    data_set = pd.DataFrame(data_set)
    return data_set


if __name__ == '__main__':
    # new_train data build
    new_log_data_set = build_data_set(NEW_LOG, 10)
    # old_log_data_set = build_data_set(OLD_LOG)
    # data_set = new_log_data_set.union(old_log_data_set)
    print(new_log_data_set.head())
    pass
