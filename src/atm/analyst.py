from sentence_transformers import SentenceTransformer, util
from atm.device import Device
from atm.utils import FunctionWrap
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

attributes = {
    'text',
    'content-desc',
    'resource-id'
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


# widget_attempt_action_map = {
#     'ImageView': ['click', 'long_click', ],
#     'EditText': ['set_text'],
#     'TextView': ['click'],
#     'Button': ['click', 'long_click', ],
#     'ImageButton': ['click', 'long_click', ],
#     'CheckBox': ['click']
# }
#
#
# def get_action_based_classes(node: et.Element):
#     class_ = node.get('class')
#     class_ = class_[class_.rfind('.') + 1:]
#     if class_ in widget_attempt_action_map:
#         return widget_attempt_action_map[class_]
#     else:
#         return ['click']


def average_cos(result):
    return sum(result) / len(result)


non_action_view = {
    'Layout',
    'Group',
    'Recycle',
    'Scroll'
}

SELECT_MOST_DIRECT = 'most_direct'
SELECT_ALL = 'all'
CALCULATE_MAX = 'max'
CALCULATE_AVERAGE = 'average'
SBERT = 'sbert'
BERT = 'model'
select_function = {
    SELECT_MOST_DIRECT: get_most_important_attribute,
    SELECT_ALL: get_node_attribute_values
}
calculate_function = {
    CALCULATE_MAX: max,
    CALCULATE_AVERAGE: average_cos
}
predict_function = {
    SBERT: predict_use_sbert,
    BERT: predict_use_bert
}


class Analyst:
    def __init__(self, device: Device, graph, select_strategy=SELECT_ALL, calculate_strategy=CALCULATE_MAX,
                 predict_model=SBERT):
        self.select_strategy = select_strategy
        self.calculate_strategy = calculate_strategy
        self.predict_model = predict_model
        self.device = device
        self.graph = graph

    def calculate_similarity(self, description, widget):
        pass

    def calculate_path_between_activity(self, source, target, description):
        pass

    def dynamic_match_widget(self, description):
        gui = self.device.get_gui()
        root = et.fromstring(gui)
        analyst_log.info('transfer gui and record to model')

        nlp = spacy.load('en_core_web_sm')
        doc = nlp(description)
        actions = []
        for token in doc:
            if token.pos_ == 'VERB':
                actions.append(token)
        ui_infos = []
        for action in actions:
            ui_info = [child for child in action.children][0]
            ui_info = ' '.join([child.text for child in ui_info.subtree])
            ui_infos.append(ui_info)
        if len(ui_infos) == 0:
            ui_infos.append(description)
        for ui_info in ui_infos:
            pass

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

    def static_match_activity(self, description):
        pass

    def valid_path(self):
        pass

    def confidence(self, node: et.Element, description):
        keys = self.select_attribute(node)
        sim = self.predict(description, keys)
        return NodeWithConfidence(node, self.calculate_score(sim))

    def select_attribute(self, node):
        return select_function[self.select_strategy](node)

    def calculate_score(self, score):
        return calculate_function[self.calculate_strategy](score)

    def predict(self, description, keys):
        return predict_function[self.predict_model](description, keys)
