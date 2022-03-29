from atm.device import Device
from atm.utils import FunctionWrap
from atm.db import DataBase
from atm.widget import Widget
from atm.construct import Constructor
from atm.FSM import FSM
import logging
import xml.etree.ElementTree as et

analyst_log = logging.getLogger('analyst')
analyst_log.setLevel(logging.DEBUG)
analyst_log_ch = logging.StreamHandler()
analyst_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
analyst_log_ch.setFormatter(formatter)
analyst_log.addHandler(analyst_log_ch)

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


class Analyst:
    def __init__(self, device: Device, graph: FSM, data_base: DataBase, confidence):
        self.confidence = confidence
        self.device = device
        self.graph = graph
        self.db = data_base
        self.constructor = Constructor(self.db)

    def calculate_path_between_activity(self, description, widget):

        paths = self.graph.find_path_to_target_widget(self.device, widget)
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

    # TODO
    def event_expansion(self, description, last_widget):
        # 1. find similarity widget between description and last_widget
        # 2. add edge into graph
        # 3. return widget into path
        pass

    # TODO
    def valid_path(self, path, description, w_target):
        widgets = []
        scores = []
        for index, event_data in enumerate(path):
            selector = event_data.selector
            action = event_data.action
            if self.device.exists_widget(selector):
                w = Widget(selector)
                e = self.constructor.generate_events_from_widget(w, action)
                widgets.append(w)
                # TODO
                # scores.append(self.confidence(w, description))
                self.device.execute(e)
                self.event_expansion(description, w)
            else:
                return False, []
        if self.device.exists_widget(w_target.to_selector):
            return

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
            lambda x: self.confidence.confidence_with_widget(x, description)
        ).append(
            sorted,
            lambda x: -x.confidence
        )
        candidate = f.do()
        return candidate

    def help(self):
        pass
