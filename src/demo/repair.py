"""
this class will give confidence between query and given node
"""
from demo.series import Series
from demo.device import Device
from demo.event import event_init_map
from utils.common import FunctionWrap
from copy import deepcopy
from functools import reduce
from bert.api import predict_two_sentence
from collections import namedtuple
import logging
import xml.etree.ElementTree as et

repair_log = logging.getLogger('repair')
repair_log.setLevel(logging.DEBUG)
repair_log_ch = logging.StreamHandler()
repair_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
repair_log_ch.setFormatter(formatter)
repair_log.addHandler(repair_log_ch)

# TODO fill the map
action_attrib_map = {
    'set_text': ['enabled', 'focusable'],
    'click': ['enable'],
    'check': ['checkable'],
    'double_click': ['enable'],
    'long_click': ['longClickable'],
    'swipe': [],
    'drag': [],
}

attributes = {
    'text',
    'content-desc',
    'resource-id'
}

NodeWithConfidence = namedtuple('NodeWithConfidence', ['node', 'confidence'])


# todo confidence and get_note_attribute is rough
def confidence(node: et.Element, description):
    result = (
        lambda x: [predict_two_sentence(description, attribute)[0] for attribute in get_node_attribute(x).values()])(
        node)
    result.sort(key=lambda x: -x)
    return NodeWithConfidence(node, result[0])


def get_node_attribute(node: et.Element):
    d = dict()
    for key in attributes:
        d[key] = node.get(key, None)
    return d


class Repair:
    def __init__(self, strategy):
        self.strategy = strategy
        pass

    @staticmethod
    def select(gui, record):
        root = et.fromstringlist(gui)
        repair_log.info('transfer gui and record to bert...')
        f = FunctionWrap((_node for _node in root.iter()))
        f.append(
        #     filter,
        #     lambda _node:
        #     FunctionWrap(
        #         f=reduce,
        #         _lambda=lambda x, y: x and y,
        #         _data=FunctionWrap(
        #             f=map,
        #             # todo the filter is depended on u2.dump, but the info is not accuracy
        #             _lambda=lambda key: True if _node.get(key, None) == 'true' else False,
        #             _data=action_attrib_map[record.action]
        #         ).iter()
        #     ).do()
        # ).append(
            map,
            lambda x: confidence(x, record.description)
        ).append(
            sorted,
            lambda x: -x.confidence
        )
        repair_log.info('filter: filter by action_map_key')
        nodes_with_confidence = f.do()
        for node_with_conf in nodes_with_confidence:
            selector = get_node_attribute(node_with_conf.node)
            _ = deepcopy(record)
            _.selector = selector
            yield event_init_map[_.action](_)

    @staticmethod
    def construct_event_series(device: Device, record_series):
        yield 1
        pass

    def combine_select(self, es1, es2):
        pass

    # need a return format
    def recovery(self, series: Series, device: Device, record_index):
        if self.strategy == 'try_next':
            return series[record_index + 1]
        elif self.strategy == 'ERROR_RECOVERY':
            record_series = series.get_direct_record_series(record_index)
            relate_index = series.get_relate_index(record_index)
            device.stop_and_restart(series.get_before_record_series(record_index))
            # the line below is error, need to execute the all repair event in executor.
            _, _ = device.execute([record.event for record in record_index[: relate_index - 1]])
            # first: try to repair the last event
            # second: try to repair the whole event_series
            gui = device.get_ui_info()
            for event in self.select(gui, series[record_index - 1]):
                device.execute(event)
                _, result = device.execute(series[record_index].event)
                if result:
                    return [event], series[record_index].event
            # TODO whether to search?
            device.stop_and_restart(series.get_before_record_series(record_index))
            for event in self.construct_event_series(device, record_series):
                device.execute(event)
            return list(self.construct_event_series(device, record_series))

    def add_new_event(self, requirement):
        pass
