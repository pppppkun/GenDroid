from sentence_transformers import SentenceTransformer, util
from atm.device import Device
from atm.utils import FunctionWrap, IRRELEVANT_WORDS
from atm.db import DataBase
from atm.widget import Widget
import spacy
import re
from collections import namedtuple
import logging
import xml.etree.ElementTree as et

analyst_log = logging.getLogger('analyst')
analyst_log.setLevel(logging.DEBUG)
analyst_log_ch = logging.StreamHandler()
analyst_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
analyst_log_ch.setFormatter(formatter)
analyst_log.addHandler(analyst_log_ch)

KEY_ATTRIBUTES = {
    'text',
    'content-desc',
    'resource-id',
    'hint'
}

PLACE_HOLDER = '@'

resource_id_pattern = re.compile(r'.*:id/(.*)')
NodeWithConfidence = namedtuple('NodeWithConfidence', ['node', 'confidence'])
model = SentenceTransformer('all-MiniLM-L6-v2')


def predict_use_sbert(description, keys):
    emd1 = model.encode(description)
    emd2 = model.encode(keys)
    cos_sim = sorted(util.cos_sim(emd1, emd2)[0], key=lambda x: -x)
    return cos_sim


def predict_use_bert(description, keys):
    from model.bert.api import predict_two_sentence
    # manhattan_sim = [predict_two_sentence(description, key)[0] for key in keys]
    # manhattan_sim.sort(key=lambda x: -x)
    manhattan_sim = predict_two_sentence(description, keys)[0]
    return manhattan_sim


def get_most_important_attribute(node: et.Element):
    if node.get('text') != '':
        return [node.get('text')]
    if node.get('content-desc') != '':
        return [node.get('content-desc')]
    # resource-id="com.android.systemui:id/navigation_bar_frame"
    if node.get('resource-id') != '':
        return [resource_id_pattern.match(node.get('resource-id')).group(1).replace('/', ' ').replace('_', ' ')]
    return [PLACE_HOLDER]


def get_node_attribute_values(node: et.Element):
    text = node.get('text')
    content_desc = node.get('content-desc')
    if node.get('resource-id') != '':
        if resource_id_pattern.match(node.get('resource-id')) is None:
            resource_id = ''
        else:
            resource_id = resource_id_pattern.match(node.get('resource-id')).group(1).replace('/', ' ').replace('_',
                                                                                                                ' ')
    else:
        resource_id = ''
    result = [text, content_desc, resource_id]
    result = list(filter(lambda x: len(x) != 0, result))
    for i in range(len(result)):
        if 'fab' in result[i]:
            result[i] = result[i].replace('fab', '')
    if len(result) == 0:
        result.append(PLACE_HOLDER)
    return result


def get_attribute_based_class(node: et.Element):
    candidate = None
    if 'text' in node.get('class').lower():
        candidate = [node.get(attr) for attr in KEY_ATTRIBUTES]
    elif 'image' in node.get('class').lower():
        candidate = [node.get(attr) for attr in KEY_ATTRIBUTES.difference('text')]
    elif 'button' in node.get('class').lower():
        candidate = [node.get(attr) for attr in KEY_ATTRIBUTES]
    else:
        candidate = [node.get(attr) for attr in KEY_ATTRIBUTES]
    candidate = list(filter(lambda x: x != '' and x is not None, candidate))
    if len(candidate) == 0:
        candidate.append(PLACE_HOLDER)
    return candidate


def get_selector_from_dynamic_edge(criteria):
    a = ['text', 'content-desc', 'resource-id']
    selectors = dict()
    for attribute in a:
        assert attribute in criteria
        selectors[attribute] = criteria[attribute]
    return selectors


def postprocess_keys(keys):
    result = []
    for key in keys:
        key = str(key)
        words = key.split('_')
        key = []
        for word in words:
            if word not in IRRELEVANT_WORDS:
                key.append(word)
        result.append(' '.join(key))
    return result


non_action_view = {
    'Layout',
    'Group',
    'Recycle',
    'Scroll'
}


def filter_by_class(node: et.Element):
    class_ = node.get('class')
    if class_ is None:
        return False
    result = True
    for view in non_action_view:
        if view in class_:
            result = False
            break
    return result


SELECT_MOST_DIRECT = 'most_direct'
SELECT_ALL = 'all'
SELECT_BASED_CLASS = 'class'
CALCULATE_MAX = 'max'
CALCULATE_AVERAGE = 'average'
SBERT = 'sbert'
BERT = 'model'
select_function = {
    SELECT_MOST_DIRECT: get_most_important_attribute,
    SELECT_ALL: get_node_attribute_values,
    SELECT_BASED_CLASS: get_attribute_based_class
}
calculate_function = {
    CALCULATE_MAX: max,
    CALCULATE_AVERAGE: lambda x: sum(x) / len(x)
}
predict_function = {
    SBERT: predict_use_sbert,
    BERT: predict_use_bert
}


class Analyst:
    def __init__(self, device: Device, graph, data_base: DataBase, select_strategy=SELECT_BASED_CLASS,
                 calculate_strategy=CALCULATE_AVERAGE,
                 predict_model=SBERT):
        self.select_strategy = select_strategy
        self.calculate_strategy = calculate_strategy
        self.predict_model = predict_model
        self.device = device
        self.graph = graph
        self.db = data_base

    def calculate_similarity(self, description, widget):
        pass

    def calculate_path_between_activity(self, source, target, description, widget):
        paths = self.graph.find_path_between_activity(source, target)
        candidate = []

        def calculate_weight(path, score):
            import numpy as np
            return np.average(score) / (1 + np.log2(len(path)))

        for path in paths:
            cp = self.device.set_checkpoint()
            widgets, score = self.valid_path(path, description, widget)
            if len(widgets) != 0:
                candidate.append([widgets, score])
            self.device.reset(cp)
        # TODO
        if len(candidate) >= 1:
            for path in candidate:
                p, s = path[0], path[1]
                # s.append(self.confidence(widget, description))
                path.append(calculate_weight(p, s))
            sorted(candidate, key=lambda x: -x[2])
            return candidate[0]
        else:
            return None

    def dynamic_match_widget(self, description):
        gui = self.device.get_gui()
        root = et.fromstring(gui)
        analyst_log.info('transfer gui and record to model')

        f = FunctionWrap((_node for _node in root.iter()))
        f.append(
            filter,
            lambda _node: filter_by_class(_node)
        ).append(
            map,
            lambda x: self.confidence(x, description)
        ).append(
            sorted,
            lambda x: -x.confidence
        )
        # return f.do()
        queue = f.do()
        widget = Widget(queue[0].node.attrib)
        return widget

    def static_match_activity(self, description):
        f = FunctionWrap(self.db.widgets)
        f.append(
            map,
            lambda x: self.confidence(x, description)
        ).append(
            sorted,
            lambda x: -x.confidence
        )
        candidate = f.do()
        return candidate

    @classmethod
    def pos_analysis(cls, description):
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(description)
        actions = []
        for token in doc:
            if token.pos_ == 'VERB':
                actions.append(token)
        ui_infos = []
        for action in actions:
            ui_info = [child for child in action.children]
            if len(ui_info) == 0:
                ui_infos.append('')
            else:
                ui_info = ui_info[0]
                ui_info = ' '.join([child.text for child in ui_info.subtree])
                ui_infos.append(ui_info)
        if len(ui_infos) == 0:
            ui_infos.append(description)
        return actions, ui_infos

    def valid_path(self, path, description, w_target):
        stepping = []
        score = []
        for index, node in enumerate(path):
            if '(' in node:
                if node.startswith('D@'):
                    # D@a=b&c=e ${action}
                    # k_v -> a = b
                    action = node.split()[1]
                    criteria = dict(
                        map(lambda k_v: (k_v.split('=')[0], k_v.split('=')[1]), node.split()[0][2:].split('&')))
                    analyst_log.log('D@criteria: ' + criteria.__str__())
                    widget = self.device.select_widget_wrapper(get_selector_from_dynamic_edge(criteria))
                else:
                    # resource-id actually
                    action = node.split('(')[1][:-1]
                    widget_name = self.db.get_widget_name_from_id(node.split()[0])
                    widget = self.device.select_widget_wrapper({'resource-id': widget_name})
                if not widget:
                    return False, []
                    # if not widget:
                #     if path[:index + 1] not in invalid_paths:
                #         invalid_paths.append(path[: index + 1])
                #     return None
                # TODO
                pre_info = self.device.app_current()
                if 'Long' in action or 'long' in action:
                    widget.long_click()
                else:
                    widget.click()
                post_info = self.device.app_current()
                stepping.append(widget)
                score.append(self.confidence(widget, description))
                self.db.update_widget(widget, pre_info['activity'])
                self.graph.add_edge(pre_info['package'] + pre_info['activity'],
                                    post_info['package'] + post_info['activity'], widget)
        # check target widget exists
        # if self.device.exists_widget(w_target):
        #     # may get bro widget.
        #     # TODO
        #     # cache_nearest_button_to_text
        #     return True, score
        # else:
        #     return False, []
        if self.device.exists_widget(w_target):
            return stepping, score
        else:
            return [], []

    def confidence(self, node: et.Element, description):
        actions, ui_infos = self.pos_analysis(description)

        # child
        childs = list(node)
        childs.append(node)
        max_score = -1
        max_node = None
        for candidate in childs:
            self.db.get_widget_id_from_name(candidate.get('resource-id'))
            keys = self.select_attribute(candidate)
            postprocess_keys(keys)
            try:
                sim = self.predict(description, keys)
            except RuntimeError:
                analyst_log.error(f'cannot be multiplied between: {keys} {description}')
                continue
            score = self.calculate_score(sim)
            if score > max_score:
                max_score = score
                max_node = candidate
            elif score == max_score:
                analyst_log.warning(f'same score between: {max_node} {candidate}')
        return NodeWithConfidence(max_node, max_score)

    def help(self):
        pass

    def select_attribute(self, node):
        return select_function[self.select_strategy](node)

    def calculate_score(self, score):
        return calculate_function[self.calculate_strategy](score)

    def predict(self, description, keys):
        return predict_function[self.predict_model](description, keys)


if __name__ == '__main__':
    description = 'create new task'
    t1 = 'ADD NEW TASK &gt;'
    r1 = 'second alert'
    t2 = ''
    r2 = 'new task'
    s1 = (predict_use_sbert(description, t1)[0] + predict_use_sbert(description, r1)[0]) / 2
    s2 = (predict_use_sbert(description, t2)[0] + predict_use_sbert(description, r2)[0]) / 2
    print(s1)
    print(s2)
