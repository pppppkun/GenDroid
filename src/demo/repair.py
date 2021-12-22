"""
this class will give confidence between query and given node
"""
from demo.series import Series
from demo.device import Device
from demo.record import Record
from demo.event import event_init_map
from copy import deepcopy
from functools import reduce
from bert.api import predict_two_sentence
import xml.etree.ElementTree as et

# TODO fill the map
action_attrib_map = {
    'set_text': ['enabled', 'focusable'],
    'click': ['clickable'],
    'check': ['checkable'],
    'double_click': ['clickable'],
    'long_click': ['longClickable'],
    'swipe': [],
    'drag': [],
}

attributes = {
    'text',
    'content-desc',
    'resource-id'
}


def confidence(node: et.Element, description):
    result = (
        lambda x: [predict_two_sentence(description, attribute)[0] for attribute in get_node_attribute(x).values()])(
        node)
    result.sort(key=lambda x: -x)
    return result[0]


def get_node_attribute(node: et.Element):
    d = dict()
    for key in attributes:
        d[key] = node.get(key, None)
    return d


class FunctionWrap:
    def __init__(self, _data, f=None, _lambda=None):
        self.data = _data
        if f is None:
            self.f = None
        else:
            self.f = f(_lambda, _data)

    def append(self, f, _lambda):
        if self.f is None:
            self.f = f(_lambda, self.data)
        elif f is sorted:
            self.f = sorted(self.f, key=_lambda)
        else:
            self.f = f(_lambda, self.f)
        return self

    def iter(self):
        return self.f

    def do(self):
        if type(self.f) is not filter and type(self.f) is not map:
            return self.f
        else:
            return list(self.f)


class Repair:
    def __init__(self, strategy):
        self.strategy = strategy
        pass

    @staticmethod
    def select(gui, record):
        root = et.fromstringlist(gui)
        f = FunctionWrap((_node for _node in root.iter()))
        f.append(
            filter,
            lambda _node:
            FunctionWrap(
                f=reduce,
                _lambda=lambda x, y: x and y,
                _data=FunctionWrap(
                    f=map,
                    _lambda=lambda key: True if _node.get(key) == 'true' else False,
                    _data=action_attrib_map[record.action]
                ).iter()
            ).do()
        ).append(
            filter,
            lambda _node: _node.get('package') == record.current_info['package']
        ).append(
            map,
            lambda x: (x, confidence(x, record.description))
        ).append(
            sorted,
            lambda x: -x[1]
        )
        nodes_with_confidence = f.do()
        # todo construct a event(action equals record.action, selector construct by widget)
        for node_with_conf in nodes_with_confidence:
            selector = get_node_attribute(node_with_conf[0])
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
