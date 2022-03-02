"""
this class will give confidence between query and given node
"""
from demo.event import event_factory, VirtualEvent, EventData
from demo.analyst import analyst
from utils.common import FunctionWrap
from copy import deepcopy
from collections import deque
from sentence_transformers import SentenceTransformer, util
from functools import reduce
import re
from collections import namedtuple
import logging
import xml.etree.ElementTree as et

construct_log = logging.getLogger('construct')
construct_log.setLevel(logging.DEBUG)
construct_log_ch = logging.StreamHandler()
construct_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
construct_log_ch.setFormatter(formatter)
construct_log.addHandler(construct_log_ch)

attributes = {
    'text',
    'content-desc',
    'resource-id'
}

PLACE_HOLDER = '@'

resource_id_pattern = re.compile(r'.*:id/(.*)')
NodeWithConfidence = namedtuple('NodeWithConfidence', ['node', 'confidence'])
model = SentenceTransformer('all-MiniLM-L6-v2')

widget_attempt_action_map = {
    'ImageView': ['click', 'long_click', ],
    'EditText': ['set_text'],
    'TextView': ['click'],
    'Button': ['click', 'long_click', ],
    'ImageButton': ['click', 'long_click', ],
    'CheckBox': ['click']
}


def predict_use_sbert(description, keys):
    emd1 = model.encode(description)
    emd2 = model.encode(keys)
    cos_sim = sorted(util.cos_sim(emd1, emd2)[0], key=lambda x: -x)
    return cos_sim


def predict_use_bert(description, keys):
    from model.api import predict_two_sentence
    manhattan_sim = [predict_two_sentence(description, key)[0] for key in keys]
    manhattan_sim.sort(key=lambda x: -x)
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


def get_node_attribute(node: et.Element):
    d = dict()
    for key in attributes:
        d[key] = node.get(key, None)
    return d


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
    if len(result) == 0:
        result.append(PLACE_HOLDER)
    return result


def average_cos(result):
    return sum(result) / len(result)


def get_action_based_classes(node: et.Element):
    class_ = node.get('class')
    class_ = class_[class_.rfind('.') + 1:]
    if class_ in widget_attempt_action_map:
        return widget_attempt_action_map[class_]
    else:
        return ['click']


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


class Constructor:
    def __init__(self, select_strategy=SELECT_ALL, calculate_strategy=CALCULATE_MAX, predict_model=SBERT):
        self.select_strategy = select_strategy
        self.calculate_strategy = calculate_strategy
        self.predict_model = predict_model
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

    # TODO more freestyle description
    def construct(self, gui, v_event: VirtualEvent):
        # nlp = spacy.load('en_core_web_sm')
        # doc = nlp(record.description)
        # action = ''
        # for token in doc:
        #     if token.pos_ == 'VERB':
        #         action = token
        #         break
        #
        # if action != '':
        #     action = \
        #         sorted(
        #             list(map(lambda action_: (action_, predict_use_sbert(action.text, action_.replace('_', ' '))[0]),
        #                      ACTIONS)),
        #             key=lambda x: -x[1])[0][0]
        #     if action in SET_ACTIONS:
        #         action = 'set_text'
        #     action.replace(' ', '_')
        #
        # ui_info = [child for child in action.children][0]
        # ui_info = ' '.join([child.text for child in ui_info.subtree])
        ui_info = v_event.description
        root = et.fromstringlist(gui)
        construct_log.info('transfer gui and record to model')

        def create_event(node_with_confidence, data=None):
            result = list()
            selector = get_node_attribute(node_with_confidence.node)
            # action should study from history (ie same widget have same action, new widget should consider the
            # static analysis result)
            action = analyst.action_analysis(node_with_confidence.node)
            if action == 'set_text' and data is None:
                data = 'place holder'
            event_data = EventData(action=action, selector=selector, data=data)
            try:
                event_ = event_factory[action](event_data)
                event_.confidence = node_with_confidence.confidence
                result.append(event_)
                return result
            except:
                construct_log.error(action, selector, data)

        f = FunctionWrap((_node for _node in root.iter()))
        f.append(
            filter,
            lambda _node: filter_by_class(_node)
        ).append(
            map,
            lambda x: self.confidence(x, ui_info)
        ).append(
            sorted,
            lambda x: -x.confidence
        ).append(
            map,
            lambda x: create_event(x, v_event.data)
        ).append(
            reduce,
            lambda x, y: x + y
        )
        events = f.do()
        return deque(events)


if __name__ == '__main__':
    pass
