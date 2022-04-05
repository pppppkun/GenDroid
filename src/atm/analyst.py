from atm.device import Device
from atm.utils import FunctionWrap
from atm.db import DataBase
from atm.widget import Widget
from atm.construct import Constructor
from atm.FSM import FSM
from atm.event import KEY_EVENTS
from atm.event import EventData
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

        paths = self.graph.find_path_to_target_widget(self.device, widget)[:2]
        candidate = []

        def calculate_weight(path, score):
            import numpy as np
            return np.average(score) / (1 + np.log2(len(path)))

        analyst_log.info('begin to valid path')
        cp = self.device.set_checkpoint()
        i = 0
        for path in paths:
            analyst_log.info(f'valid {i}-th path')
            i += 1
            events, scores = self.valid_path(path, description, widget)
            if events:
                candidate.append([events, scores])
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
    # fix: should remove same widget in path
    def event_expansion(self, description, last_selector: dict):
        # 1. find similarity widget between description and last_widget
        # 2. add edge into graph
        # 3. return widget into path
        # only support edittext now.
        # search brother node.
        # search
        gui = self.device.gui()
        gui = et.fromstring(gui)
        target_parent = None
        direct_brother = None
        candidate_edit_text = []
        queue = [gui]
        cluster = []
        while len(queue) != 0:
            parent = queue.pop(0)
            children = list(parent)
            queue += children
            for node in children:
                if 'EditText' in node.get('class'):
                    candidate_edit_text.append(node)
        if 'EditText' in last_selector['class']:
            need_remove = None
            for edit_text in candidate_edit_text:
                if edit_text.get('resource-id') == last_selector['resource-id'] and \
                        edit_text.get('content-desc') == last_selector['content-desc']:
                    # don't modify same widget at same time
                    need_remove = edit_text
                    break
            if need_remove is not None:
                candidate_edit_text.remove(need_remove)
        candidate_edit_text = sorted(
            map(
                lambda x: [x, self.confidence.confidence_with_node(x, description)],
                candidate_edit_text
            ),
            key=lambda x: -x[1].confidence
        )
        if len(candidate_edit_text) == 0:
            return [], []
        target_widget = candidate_edit_text[0][0]
        # find cluster
        queue = [gui]
        while len(queue) != 0:
            parent = queue.pop(0)
            children = list(parent)
            queue += children
            for node in children:
                if node == target_widget:
                    for brother in children:
                        if 'EditText' in brother.get('class'):
                            cluster.append(brother)
                    break
            if len(cluster) != 0:
                break
        assert len(cluster) != 0
        scores = list(map(lambda x: self.confidence.confidence_with_node(x, description).confidence, cluster))
        return cluster, scores

    def valid_path(self, path, description, w_target):
        events = []
        scores = []
        for index, event_data in enumerate(path):
            selector = event_data.selector
            action = event_data.action
            if action in KEY_EVENTS:
                analyst_log.info(f'check {len(events)}-th event with action={action}')
                event = Constructor.generate_event_from_event_data(event_data)
                self.device.execute(event, is_add_edge=False)
                # scores.append(
                #     self.confidence.confidence_with_selector(last_widget, description))
                events.append(event)
                continue
            if self.device.exists_widget(selector):
                event = Constructor.generate_event_from_event_data(event_data)
                last_widget = self.device.select_widget_wrapper(selector)
                analyst_log.info(f'check {len(events)}-th event with action={action} rid={last_widget["resource-id"]}')
                scores.append(
                    self.confidence.confidence_with_selector(last_widget, description).confidence)
                events.append(event)
                self.device.execute(event, is_add_edge=False)
                ns, ss = self.event_expansion(description, last_widget)
                es = list(
                    map(lambda x: self.constructor.generate_event_from_node(x, action='set_text',
                                                                            data={'text': 'hello'}),
                        ns
                        ),
                )
                self.device.execute(es)
                scores += ss
                events += es
            else:
                return None, None
        t = self.device.exists_widget(w_target.to_selector())
        # print(type(t), t)
        if t:
            return events, scores
        else:
            return None, None

    def dynamic_match_widget(self, description):
        """
        return GUI element with the highest confidence
        :param description:
        :return:
        """
        gui = self.device.gui()
        root = et.fromstring(gui)
        analyst_log.info('transfer gui and record to model')

        f = FunctionWrap((_node for _node in root.iter()))
        f.append(
            filter,
            lambda _node: filter_by_class(_node)
        ).append(
            map,
            lambda x: self.confidence.confidence_with_node(x, description)
        ).append(
            sorted,
            lambda x: -x.confidence
        )
        # return f.do()
        queue = f.do()
        widget = Widget(queue[0].node.attrib)
        return widget

    def static_match_activity(self, description):
        """
        return [widget_0, widget_1, ... ]
        :param description:
        :return:
        """
        f = FunctionWrap(self.db.widgets)
        analyst_log.info('calculate similarity between description and static widget')
        f.append(
            map,
            lambda x: self.confidence.confidence_with_widget(x, description)
        ).append(
            sorted,
            lambda x: -x.confidence
        ).append(
            map,
            lambda x: x.node
            # lambda x : x
        )
        candidate = f.do()
        # r_end = 5 if len(candidate) > 5 else len(candidate)
        return candidate

    def help(self):
        pass
