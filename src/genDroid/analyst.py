import traceback

from genDroid.device import Device
from genDroid.utils import FunctionWrap
from genDroid.db import DataBase
from genDroid.widget import Widget
from genDroid.construct import Constructor
from genDroid.FSM import FSM
from genDroid.event import KEY_EVENTS
from genDroid.utils import ICON_SEMANTIC
from src.model.icon_semantic import class_index
import copy
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
    'Scroll',
    'SeekBar'
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
        self.path_count_threshold = 1
        self.mode = ''

    def try_back_without_restart(self, events, state):
        analyst_log.info('try back to checkpoint without restart')
        index = len(events) - 1
        while index >= 0:
            event = events[index]
            new_event = copy.deepcopy(event)
            if event.action == 'back':
                if index >= 2:
                    index -= 2
                if index < 2:
                    # todo find a way from snow -> sA
                    # briefly return false now
                    return False
            elif event.action == 'set_text':
                new_event.text = ''
                pass
            elif event.action == 'click':
                selector = event.selector
                widget = self.device.select_widget_wrapper(selector)
                if 'checkbox' in widget['class'].lower():
                    new_event.action = 'click'
                # 1. checkbox
                # 2. button
                new_event.action = 'back'
                pass
            else:
                return False
            _, result = self.device.execute(new_event, is_add_edge=False)
            if not result:
                return False

        now_state, match = self.graph.get_most_closest_state(self.device.app_current_with_gui())
        return now_state.id == state.id

    def calculate_path_between_activity(self, description, widget):

        paths = self.graph.find_path_to_target_widget(self.device, widget)
        candidate = []

        def calculate_weight(path, score):
            import numpy as np
            if len(score) == 0:
                return 0
            return np.average(score) / (1 + np.log2(len(path)))

        analyst_log.info(f'find {len(paths)} paths')
        if len(paths) == 0:
            return None
        analyst_log.info('begin to valid path')
        cp = self.device.set_checkpoint()
        state, _ = self.graph.get_most_closest_state(self.device.app_current_with_gui())
        i = 0
        for path in paths:
            if i == self.path_count_threshold:
                break
            analyst_log.info(f'valid {i}-th path')
            i += 1
            events, scores = self.valid_path(path, description, widget)
            if events and scores:
                candidate.append([events, scores])
            if self.try_back_without_restart(events, state):
                continue
            self.device.reset(cp)
            if len(candidate) == 5:
                break

        if len(candidate) >= 1:
            for path in candidate:
                p, s = path[0], path[1]
                # s.append(self.confidence(widget, description))
                path.append(calculate_weight(p, s))
            sorted(candidate, key=lambda x: -x[2])
            return candidate[0]
        else:
            return None

    # fix: should remove same widget in path
    def event_expansion(self, description, will_or_have_execute_event_selector=None):

        # 1. find edit text
        # 2. 2 situation

        gui = self.device.gui()
        gui = et.fromstring(gui)
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

        if len(candidate_edit_text) == 0:
            return [], []

        candidate_edit_text = sorted(
            map(
                lambda x: [x, self.confidence.confidence_with_node(x, description)],
                candidate_edit_text
            ),
            key=lambda x: -x[1].confidence
        )

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
                            db_widget = self.db.get_origin_widget_text(brother.get('resource-id'))
                            if db_widget:
                                if db_widget.hint.upper() == brother.get('text').upper():
                                    cluster.append(brother)
                            else:
                                cluster.append(brother)
                    break
            if len(cluster) != 0:
                break

        need_to_remove = []
        if will_or_have_execute_event_selector:
            for node in cluster:
                for selector in will_or_have_execute_event_selector:
                    if node.get('resource-id') == selector['resource-id']:
                        need_to_remove.append(node)
            for node in need_to_remove:
                if node in cluster:
                    cluster.remove(node)

        if len(cluster) == 0:
            return [], []

        for node in cluster:
            analyst_log.info(f'event expansion with {node.get("resource-id")}')

        last_event = self.device.history[-1]
        if last_event.selector:
            cluster = list(filter(lambda x: x.get('resource-id') != last_event.selector['resource-id'], cluster))
        scores = list(map(lambda x: self.confidence.confidence_with_node(x, description).confidence, cluster))
        return cluster, scores

    def valid_path(self, path, description, w_target: dict):
        try:
            events = []
            scores = []
            will_or_have_execute_event_selector = [event_data.selector for event_data in path if event_data.selector]
            for index, event_data in enumerate(path):
                ns, ss = self.event_expansion(description, None)
                es = list(
                    map(lambda x: self.constructor.generate_event_from_node(x, action='set_text',
                                                                            data={'text': 'hello'}),
                        ns
                        ),
                )
                self.device.execute(es)
                scores += ss
                events += es
                will_or_have_execute_event_selector += [e.selector for e in es]
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
                    analyst_log.info(
                        f'check {len(events)}-th event with action={action} rid={last_widget["resource-id"]}')
                    scores.append(
                        self.confidence.confidence_with_selector(last_widget, description).confidence)
                    events.append(event)
                    self.device.execute(event, is_add_edge=False)

                else:
                    analyst_log.info(f'can\'t find widget {selector["resource-id"]} in valid')
                    return events, None
            t = self.device.exists_widget(w_target)
            if t:
                analyst_log.info('successfully valid path')
                return events, scores
            else:
                analyst_log.info(f'can\'t find widget {w_target} in valid')
                return events, None
        except:
            analyst_log.info('meet unhandled error when valid path')
            traceback.print_exc()
            return events, None

    def dynamic_match_widget(self, description):
        """
        return GUI element with the highest confidence
        :param description:
        :return:
        """
        gui = self.device.gui()
        root = et.fromstring(gui)
        analyst_log.info('calculate similarity between description and GUI')
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
        # f = FunctionWrap(self.graph.widgets())
        widgets = self.graph.widgets()
        analyst_log.info(f'calculate similarity between "{description}" and static widget')
        widgets = list(filter(lambda x: x['resource-id'] and 'Layout' not in x['class'], widgets))
        count = len(widgets)
        node_with_confidences = []
        for index, widget in enumerate(widgets):
            n_w_c = self.confidence.confidence_with_selector(widget, description)
            node_with_confidences.append(n_w_c)

            if index % 20 == 0:
                analyst_log.info(f'have calculate {(index / count) * 100}% static widget...')
        node_with_confidences = sorted(node_with_confidences, key=lambda x: -x.confidence)
        node_with_confidences = map(lambda x: x.node, node_with_confidences)
        return node_with_confidences

    def analyst_mode(self, widget: Widget):
        selector = widget.to_selector()
        img = self.device.widget_screenshot(selector)
        if img is None:
            self.mode = 'none'
        else:
            import numpy as np
            tensor = np.array(img)
            index = class_index(tensor)
            self.mode = ICON_SEMANTIC[index]

    def help(self):
        pass
