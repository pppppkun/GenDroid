import re
from collections import namedtuple
import xml.etree.ElementTree as et
import spacy
import numpy as np
from sentence_transformers import SentenceTransformer, util
from genDroid.widget import Widget
from genDroid.utils import IRRELEVANT_WORDS
import enchant

d = enchant.Dict("en_US")

KEY_ATTRIBUTES = {
    'text',
    'content-desc',
    'resource-id',
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


def get_attribute_base_on_class(node: dict):
    clazz = node['class'].lower()
    text = node['text']
    content_desc = node['content-desc']
    if node['resource-id'] is None or resource_id_pattern.match(node['resource-id']) is None:
        resource_id = ''
    else:
        resource_id = resource_id_pattern.match(node['resource-id']).group(1).replace('/', ' ').replace('_',
                                                                                                        ' ')
    if 'text' in clazz:
        candidate = [text, content_desc, resource_id]
    elif 'image' in clazz:
        candidate = [content_desc, resource_id]
    elif 'button' in clazz:
        candidate = [text, content_desc, resource_id]
    else:
        candidate = [text, content_desc, resource_id]
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
        key = key.translate({
            ord(' '): '_',
            ord('-'): '_'
        })
        words = key.split('_')
        key = []
        for word in words:
            if word not in IRRELEVANT_WORDS:
                key.append(word)
        result.append(' '.join(key))
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
    SELECT_BASED_CLASS: get_attribute_base_on_class
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

    @staticmethod
    def pos_analysis(description):
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
                # ui_infos.append('')
                pass
            else:
                ui_info = ui_info[0]
                ui_info = ' '.join([child.text for child in ui_info.subtree])
                ui_infos.append(ui_info)
        if len(ui_infos) == 0:
            ui_infos.append(description)
        actions = list(map(lambda x: x.text, actions))
        return actions, ui_infos

    def confidence_with_gui(self, root: et.Element, description):
        # for node in root.iter():
        pass

    def confidence_with_node(self, node: et.Element, description):
        dic = node.attrib
        confidence = self.confidence_with_selector(dic, description).confidence
        return NodeWithConfidence(node=node, confidence=confidence)

    def confidence_with_widget(self, widget: Widget, description):
        selector = widget.to_selector()
        selector['class'] = widget.get_class()
        confidence = self.confidence_with_selector(selector, description).confidence
        return NodeWithConfidence(node=widget, confidence=confidence)

    def confidence_with_selector(self, dic: dict, description):
        assert 'resource-id' in dic
        assert 'content-desc' in dic
        assert 'text' in dic
        assert 'class' in dic
        confidence = self.__confidence(dic, description)
        return NodeWithConfidence(node=dic, confidence=confidence)

    def __confidence(self, node: dict, description):
        actions, ui_infos = self.pos_analysis(description)
        keys = self.select_attribute(node)
        keys = postprocess_keys(keys)
        result = []
        for key in keys:
            if key == PLACE_HOLDER:
                continue
            key_actions, key_ui_infos = self.pos_analysis(key)
            sims = []
            for key_action in key_actions:
                for action in actions:
                    sims.append(self.predict(key_action, action))
            for key_info in key_ui_infos:
                if key_info == '':
                    continue
                for info in ui_infos:
                    if info == '':
                        continue
                    sims.append(self.predict(key_info, info))
            # select most similar part with description
            result.append(np.max(sims))
        if len(result) == 0:
            score = 0
        else:
            score = np.average(result)
        return score
        # score = np.average(result)
        # return np.average(result)
        # return NodeWithConfidence(node=node, confidence=np.average(result))

    def select_attribute(self, node):
        return select_function[self.select_strategy](node)

    def calculate_score(self, score):
        return calculate_function[self.calculate_strategy](score)

    def predict(self, description, keys):
        return predict_function[self.predict_model](description, keys)


if __name__ == '__main__':

    d = 'Please make sure the reminders work properly before relying on them. Check your device battery and notification settings, if there is nothing blocking the reminders, or killing the app in the background.'
    s = 'confirm'
    print(predict_use_sbert(d, s))
    #     if key == PLACE_HOLDER:
    #         continue
    #     key_actions, key_ui_infos = confidence.pos_analysis(key)
    #     sims = []
    #     for key_action in key_actions:
    #         for action in actions:
    #             sims.append(self.predict(key_action, action))
    #     for key_info in key_ui_infos:
    #         if key_info == '':
    #             continue
    #         for info in ui_infos:
    #             if info == '':
    #                 continue
    #             sims.append(self.predict(key_info, info))
    #     # select most similar part with description
    #     result.append(np.max(sims))
    # if len(result) == 0:
    #     score = 0
    # else:
    #     score = np.average(result)
    # return score
