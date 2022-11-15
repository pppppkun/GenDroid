import re
from collections import namedtuple
import xml.etree.ElementTree as et
import spacy
import nltk
from nltk.corpus import stopwords
import numpy as np
from sentence_transformers import SentenceTransformer, util
from gendroid.widget import Widget
from gendroid.utils import IRRELEVANT_WORDS, safe_check_key, calculation_position, bounds2list
from joblib import load
from enum import Enum
import enchant
import logging

confidence_log = logging.getLogger('confidence')
confidence_log.setLevel(logging.DEBUG)
confidence_log_ch = logging.StreamHandler()
confidence_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
confidence_log_ch.setFormatter(formatter)
confidence_log.addHandler(confidence_log_ch)

d = enchant.Dict("en_US")
precise_nlp = spacy.load('en_core_web_trf')
quick_nlp = spacy.load('en_core_web_sm')

KEY_ATTRIBUTES = [
    'text',
    'content-desc',
    'resource-id',
]

NORMAL_ACTION = [
    'click', 'tap', 'open', 'select'
    # 'click', 'open'
]

PLACE_HOLDER = '@'

resource_id_pattern = re.compile(r'.*:id/(.*)')
NodeWithConfidence = namedtuple('NodeWithConfidence', ['node', 'confidence'])
model = SentenceTransformer('/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/output_model')
# model = SentenceTransformer('/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/all-MiniLM-L6-v2')
# model = SentenceTransformer('/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/bert/base_model')
# decision_model = load('/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/decision/rf.joblib')
decision_model = load('/Users/pkun/PycharmProjects/ui_api_automated_test/src/model/decision/classifier_lack.joblib')

def process_resource_id(x):
    r = resource_id_pattern.match(x)
    if r:
        return r.group(1).replace('/', ' ').replace('_', ' ')
    else:
        return x


def predict_use_sbert(description, keys):
    emd1 = model.encode(description)
    emd2 = model.encode(keys)
    cos_sim = sorted(util.cos_sim(emd1, emd2)[0], key=lambda x: -x)
    return cos_sim


def predict_use_bert(description, keys):
    from model.bert.api import predict_two_sentence
    manhattan_sim = predict_two_sentence(description, keys)[0]
    return manhattan_sim


def get_most_important_attribute(node: dict):
    for attribute in KEY_ATTRIBUTES:
        if safe_check_key(node, attribute):
            if attribute != 'resource-id':
                return {attribute: node[attribute]}
            else:
                return {attribute: process_resource_id(node['resource-id'])}
    return {}


def get_node_attribute_values(node: dict):
    text = node['text']
    content_desc = node['content-desc']
    if node['resource-id'] != '':
        if resource_id_pattern.match(node.get('resource-id')) is None:
            resource_id = ''
        else:
            resource_id = process_resource_id(node['resource-id'])
    else:
        resource_id = ''
    result = {'text': text, 'content-desc': content_desc, 'resource-id': resource_id}
    result = {k: v for k, v in result.items() if len(v) != 0}
    return result


def get_attribute_base_on_class(node: dict):
    clazz = node['class'].lower()
    text = node['text']
    content_desc = node['content-desc']
    if node['resource-id'] is None or resource_id_pattern.match(node['resource-id']) is None:
        resource_id = ''
    else:
        resource_id = process_resource_id(node['resource-id'])
    if 'text' in clazz:
        candidate = {'text': text, 'content-desc': content_desc, 'resource-id': resource_id}
    elif 'image' in clazz:
        candidate = {'content-desc': content_desc, 'resource-id': resource_id}
    elif 'button' in clazz:
        candidate = {'text': text, 'content-desc': content_desc, 'resource-id': resource_id}
    else:
        candidate = {'text': text, 'content-desc': content_desc, 'resource-id': resource_id}
    # candidate = list(filter(lambda x: x != '' and x is not None, candidate))
    candidate = {k: v for k, v in candidate.items() if len(v) != 0}
    return candidate


def get_selector_from_dynamic_edge(criteria):
    a = ['text', 'content-desc', 'resource-id']
    selectors = dict()
    for attribute in a:
        assert attribute in criteria
        selectors[attribute] = criteria[attribute]
    return selectors


def postprocess_keys(candidate: dict):
    for key in candidate:
        value = str(candidate[key])
        value = value.translate({
            ord(' '): '_',
            ord('-'): '_'
        })
        words = value.split('_')
        value = []
        for word in words:
            if word not in IRRELEVANT_WORDS:
                value.append(word)
        candidate[key] = ' '.join(value)
    return candidate


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

direction = [
    'top', 'bottom', 'upper', 'left', 'right'
]

location_words = direction + ['corner']

relative = [
    'under', 'above', 'below',
]

absolute = [
    'at', 'on', 'in'
]


class LocationType(Enum):
    NULL_LOCATION = 0
    ABSOLUTE = 1
    RELATIVE = 2
    UNRECOGNIZED = 3


class GridLocation(Enum):
    TOP_LEFT = 0
    TOP_CENTER = 1
    TOP_RIGHT = 2
    LEFT = 3
    CENTER = 4
    RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_CENTER = 7
    BOTTOM_RIGHT = 8


class Location:
    up = ['up', 'upper', 'top']

    left = ['left']

    right = ['right']

    down = ['bottom', 'under']

    center = ['center', 'near', 'in']

    map_ = {
        **{u: 1 for u in up},
        **{l: -1 for l in left},
        **{r: 1 for r in right},
        **{d: 7 for d in down},
        **{c: 4 for c in center}
    }

    def __init__(self, location_type, info):
        self.location_type = location_type
        self.info = info
        self.grid = None
        self.relative = None
        self.neighbor = None
        self.analysis()

    def analysis(self):
        self.grid = 0
        if self.location_type == LocationType.NULL_LOCATION:
            self.info = 'None location info'
        if self.location_type == LocationType.RELATIVE:
            self.info = nltk.word_tokenize(self.info)
            location = []
            for w in relative + direction:
                if w in self.info:
                    location.append(w)
                    self.info.remove(w)
            self.info = [word for word in self.info if word not in stopwords.words('english')]
            self.neighbor = ' '.join(self.info)
            for i in location:
                for key in Location.map_:
                    if i == key:
                        self.grid += Location.map_[key]
            self.relative = self.grid
        if self.location_type == LocationType.ABSOLUTE:
            location = nltk.word_tokenize(self.info)
            location = [word for word in location if word not in stopwords.words('english')]
            if 'corner' in location:
                location.remove('corner')
            for i in location:
                for key in Location.map_:
                    if i == key:
                        self.grid += Location.map_[key]
            self.grid = GridLocation(self.grid)
            self.info = ' '.join(location)

    def calculate_grid(self):
        pass

    def grid_index(self):
        if self.location_type == LocationType.ABSOLUTE:
            return self.grid.value
        if self.location_type == LocationType.RELATIVE:
            return self.grid + 10

    def __str__(self):
        if self.location_type == LocationType.NULL_LOCATION:
            return 'None Location Info'
        if self.location_type == LocationType.ABSOLUTE:
            return self.info + ' ' + self.grid.__str__()
        if self.location_type == LocationType.RELATIVE:
            return str(self.relative) + ' ' + self.neighbor


class Confidence:
    def __init__(self, select_strategy=SELECT_MOST_DIRECT,
                 calculate_strategy=CALCULATE_AVERAGE,
                 predict_model=SBERT):
        self.select_strategy = select_strategy
        self.calculate_strategy = calculate_strategy
        self.predict_model = predict_model
        self.cache = []
        pass

    @staticmethod
    def event_and_location_analysis(words):
        doc = precise_nlp(' '.join(words))
        action_word = []
        location_word = []
        for i in range(len(doc)):
            if doc[i].pos_ == 'VERB':
                action_word.append(i)
            if doc[i].pos_ == 'ADP':
                location_word.append(i)
        if len(action_word) == 0:
            for a in NORMAL_ACTION:
                if a in words:
                    action_word = [words.index(a)]
                    break
            # if 'tap' in words:
            #     action_word = [words.index('tap')]
        assert len(action_word) != 0
        # if len(action_word) == 0:
        #     action_word.append(0)
        #     print(words)
        action_index = action_word[0]
        if len(location_word) > 0:
            for index in location_word:
                if abs(action_index - index) == 1:
                    location_word.remove(index)
        if len(location_word) == 0:
            return words, None
        else:
            location_index = location_word[0]
            if action_index < location_index:
                location = doc[location_index:]
                event = doc[:location_index]
            else:
                location = doc[:action_index]
                event = doc[action_index:]
            return event.text, location.text

    @staticmethod
    def pos_analysis(description, nlp=quick_nlp):
        # spacy can't recognize tap as VERB
        if description.startswith('tap'):
            return ['tap'], [description[description.index('tap') + 4:]]
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

    @staticmethod
    def recognize_location_type(words):
        # if location_type == LocationType.NULL_LOCATION:
        location_type = LocationType.NULL_LOCATION
        # doc = precise_nlp(' '.join(words))
        # for i in range(len(doc)):
        #     if doc[i].pos_ == 'ADP' and doc[max(i-1, 0)].pos_ != 'VERB':
        #         location_type = LocationType.UNRECOGNIZED
        for i in relative:
            if i in words:
                location_type = LocationType.RELATIVE
                return location_type
        for i in absolute:
            if i in words:
                if 'of' in words:
                    location_type = LocationType.RELATIVE
                else:
                    for j in location_words:
                        if j in words:
                            location_type = LocationType.ABSOLUTE
                    return location_type
        return location_type

    @staticmethod
    def remove_meaningless_word(words):
        special_stopwords = direction + location_words + relative + absolute
        special_stopwords.append('the')
        special_stopwords.append('button')
        if type(words) == str:
            words = words.split(' ')
        words = list(filter(lambda x: x not in special_stopwords, words))
        # words = list(filter(lambda x: x == 'more' or x not in special_stopwords.words('english'), words))
        # if 'button' in words:
        #     words.remove('button')
        return words

    @staticmethod
    def analysis_description(sentence):
        words = nltk.word_tokenize(sentence)
        flag = False
        if 'back' in words and words.index('back') + 1 < len(words) and words[words.index('back') + 1] == 'up':
            words[words.index('back')] = 'backup'
            words.pop(words.index('backup') + 1)
            flag = True
        # 1. divide into (event, location)
        # event, location = Confidence.event_and_location_analysis(words)
        # if location is not None:
        #     location_type = Confidence.recognize_location_type(location.split(' '))
        #     event = nltk.word_tokenize(event)
        # else:
        #     location_type = LocationType.NULL_LOCATION
        location_type = Confidence.recognize_location_type(words)
        location = None
        if location_type != LocationType.NULL_LOCATION:
            event, location = Confidence.event_and_location_analysis(words)
            if location is None:
                location_type = LocationType.NULL_LOCATION
            else:
                event = nltk.word_tokenize(event)
        else:
            event = words
        if flag:
            index = event.index('backup')
            event.insert(index + 1, 'up')
            event[index] = 'back'
        if '@' in event:
            index = event.index('@')
            pre = event[index - 1]
            post = event[index + 1]
            event[index - 1] = pre + '@' + post
            event.pop(index)
            event.pop(index)
        # action_with_ui = ' '.join(event)
        # actions, uis = Confidence.pos_analysis(action_with_ui, precise_nlp)
        # if len(actions) != 0 and len(uis) != 0:
        #     action, ui = actions[0], uis[0]
        # else:
        #     action, ui = event[0], event[1:]
        # action, ui = Confidence.remove_meaningless_word(action), Confidence.remove_meaningless_word(ui)
        # event = list(filter(lambda x: x == 'more' or x not in stopwords.words('english'), event))
        if 'do' in event and event[event.index('do') + 1] == 'n\'t':
            event[event.index('do')] = 'don\'t'
            event.pop(event.index('don\'t') + 1)
        event = Confidence.remove_meaningless_word(event)
        action = event[0]
        ui = ' '.join(event[1:])
        location = Location(location_type, location)
        # print((action, ui_info, location.__str__()))
        return action, ui, location

    def confidence_with_gui(self, root: et.Element, description):
        # for node in root.iter():
        pass

    def confidence_with_node(self, node: et.Element, description, use_position):
        dic = node.attrib
        confidence = self.confidence_with_selector(dic, description, use_position).confidence
        return NodeWithConfidence(node=node, confidence=confidence)

    def confidence_with_widget(self, widget: Widget, description, use_position):
        selector = widget.to_selector()
        selector['class'] = widget.get_class()
        confidence = self.confidence_with_selector(selector, description, use_position).confidence
        return NodeWithConfidence(node=widget, confidence=confidence)

    def confidence_with_selector(self, dic: dict, description, use_position=False):
        assert 'resource-id' in dic
        assert 'content-desc' in dic
        assert 'text' in dic
        assert 'class' in dic
        if use_position:
            assert 'bounds' in dic
        confidence = self.__new_confidence(dic, description, use_position)
        return NodeWithConfidence(node=dic, confidence=confidence)

    def calculate_semantic_similarity(self, action, ui, attributes):
        if len(attributes) == 0:
            return -1
        attributes = postprocess_keys(attributes)
        result = []
        for k in attributes:
            v = attributes[k]
            attr_actions, attr_uis = self.pos_analysis(v)
            scores = []
            if action not in NORMAL_ACTION:
                for attr_action in attr_actions:
                    scores.append(self.predict(attr_action, action))
            for attr_ui in attr_uis:
                scores.append(self.predict(attr_ui, ui))
            scores.append(self.predict(ui, v))
            if len(scores) != 0:
                result.append(np.max(scores))
        if len(result) == 0:
            score = 0
        else:
            score = np.average(result)
        return score

    def __new_confidence(self, node: dict, description, using_position):
        action, ui, location = self.analysis_description(description)
        attributes = self.select_attribute(node)
        # print(attributes)
        semantic_similarity = self.calculate_semantic_similarity(action, ui, attributes)
        if not using_position:
            return semantic_similarity
        else:
            if semantic_similarity == -1:
                return -1
            x = [location.location_type.value]
            if location.location_type == LocationType.NULL_LOCATION:
                return semantic_similarity
            if location.location_type == LocationType.ABSOLUTE:
                x.append(location.grid.value)
                bounds = bounds2list(node['bounds'])
                x.extend(bounds)
                x.extend([0, 0, 1080, 1920])
            if location.location_type == LocationType.RELATIVE:
                x.append(location.relative)
                widget = self.select_relative_widget(location.neighbor)
                bounds = bounds2list(node['bounds'])
                x.extend(bounds)
                relative_bounds = bounds2list(widget['bounds'])
                x.extend(relative_bounds)
            x.append(round(semantic_similarity, 2))
            # result = decision_model.predict([x])
            result = decision_model.predict_proba([x])[0][1]
            # result = max(semantic_similarity, result)
            return result

    def __confidence(self, node: dict, description):
        actions, ui_infos = self.pos_analysis(description)
        attributes = self.select_attribute(node)
        if len(attributes) == 0:
            return -1
        attributes = postprocess_keys(attributes)
        result = []
        for k in attributes:
            v = attributes[k]
            attr_actions, attr_ui_infos = self.pos_analysis(v)
            scores = []
            for attr_action in attr_actions:
                for action in actions:
                    scores.append(self.predict(attr_action, action))
            for attr_ui_info in attr_ui_infos:
                if attr_ui_info == '':
                    continue
                for ui_info in ui_infos:
                    if ui_info == '':
                        continue
                    scores.append(self.predict(attr_ui_info, ui_info))
            if len(scores) != 0:
                result.append(np.max(scores))
        if len(result) == 0:
            score = 0
        else:
            score = np.average(result)
        return score

    def cache_widget(self, gui):
        self.cache = gui

    def select_relative_widget(self, description):
        result = []
        for node in self.cache:
            result.append([node, self.__confidence(node.attrib, description)])
        result = sorted(result, key=lambda x: -x[1])
        return result[0][0].attrib

    def select_attribute(self, node):
        return select_function[self.select_strategy](node)

    def calculate_score(self, score):
        return calculate_function[self.calculate_strategy](score)

    def predict(self, description, keys):
        return predict_function[self.predict_model](description, keys)
