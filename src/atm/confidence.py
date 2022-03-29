import re
from collections import namedtuple
import xml.etree.ElementTree as et

import spacy
from sentence_transformers import SentenceTransformer, util
from atm.widget import Widget
from atm.utils import IRRELEVANT_WORDS

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


class Confidence:
    def __init__(self, select_strategy=SELECT_BASED_CLASS,
                 calculate_strategy=CALCULATE_AVERAGE,
                 predict_model=SBERT):
        self.select_strategy = select_strategy
        self.calculate_strategy = calculate_strategy
        self.predict_model = predict_model
        pass

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

    # TODO
    def confidence_with_gui(self, node: et.Element, description):
        pass

    # TODO
    def confidence_with_widget(self, node: Widget, description):
        pass

    # TODO
    def confidence_with_selector(self, node: dict, description):
        assert node['class']
        assert node['resource-id']
        assert node['content-desc']
        assert node['text']
        pass

    # TODO
    def __confidence(self, node, description):
        pass
        # child
        # childs = list(node)
        # childs.append(node)
        # max_score = -1
        # max_node = None
        # for candidate in childs:
        #     self.db.get_widget_id_from_name(candidate.get('resource-id'))
        #     keys = self.select_attribute(candidate)
        #     postprocess_keys(keys)
        #     try:
        #         sim = self.predict(description, keys)
        #     except RuntimeError:
        #         # analyst_log.error(f'cannot be multiplied between: {keys} {description}')
        #         continue
        #     score = self.calculate_score(sim)
        #     if score > max_score:
        #         max_score = score
        #         max_node = candidate
        #     elif score == max_score:
        #     pass
        # # analyst_log.warning(f'same score between: {max_node} {candidate}')
        # return NodeWithConfidence(max_node, max_score)

    def select_attribute(self, node):
        return select_function[self.select_strategy](node)

    def calculate_score(self, score):
        return calculate_function[self.calculate_strategy](score)

    def predict(self, description, keys):
        return predict_function[self.predict_model](description, keys)
