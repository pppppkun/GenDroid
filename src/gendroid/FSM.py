import copy
import traceback

import gendroid.event
from gendroid.event import build_event, EventData
from bidict import bidict
from gendroid.widget import Widget
import networkx as nx
import os
import json
import re
import logging

fsm_log = logging.getLogger('FSM')
fsm_log.setLevel(logging.DEBUG)
fsm_log_ch = logging.StreamHandler()
fsm_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fsm_log_ch.setFormatter(formatter)
fsm_log.addHandler(fsm_log_ch)


class FSM:
    def __init__(self, graph_folder):
        self.graph_folder = graph_folder
        self.g = nx.MultiDiGraph()
        self.states = {}
        self.edges = {}
        self.import_graph()

    def import_graph(self):
        events = os.path.join(self.graph_folder, 'events')
        states = os.path.join(self.graph_folder, 'states')
        if not os.path.exists(events) or not os.path.exists(states):
            return
        events = [os.path.join(events, f) for f in os.listdir(events) if f.endswith('.json')]
        states = [os.path.join(states, f) for f in os.listdir(states) if f.endswith('.json')]
        for state in states:
            try:
                state = json.load(open(state, 'r'))
            except json.decoder.JSONDecodeError:
                continue
            state['type'] = State.STATIC
            state = State(state)
            self.g.add_node(state.id)
            self.states[state.id] = state
        for event in events:
            try:
                event = json.load(open(event, 'r'))
            except json.decoder.JSONDecodeError:
                continue
            event['type'] = Edge.STATIC
            edge = Edge(event)
            self.g.add_edge(edge.src, edge.tgt, edge=edge)
            self.edges[edge.event_str] = edge
        pass

    def find_path_to_target_widget(self, device, target_widget: dict):
        try:
            src, _ = self.get_most_closest_state(device.app_current_with_gui())
            if src is None:
                src = self.add_node(device.app_current_with_gui())
            if self.__have_out_edge(src):
                srcs = [src]
            else:
                fsm_log.info(f'state {src.id} have not out edge.')
                # srcs = self.__find_state_subset(src)
                # srcs = self.__find_same_activity_state(src)
                return [[]]
                # 1. find the state with same activity
                # 2. find path
                # 3. filter path using first widget.
            tgts = self.get_states_contain_widget(target_widget)
        except:
            fsm_log.error('error to find state.')
            traceback.print_exc()
            return []
        candidate = []
        for src in srcs:
            for tgt in tgts:
                fsm_log.info(f'begin to find path between {src.id} {tgt.id}')
                if tgt.id == src.id:
                    candidate += [[]]
                else:
                    candidate += self.__find_path_between_state(src, tgt)
        # for tgt in tgts:
        #     if tgt.id == src.id:
        #         candidate += []
        #     else:
        #         candidate += self.__find_path_between_state(src, tgt)
        candidate.sort(key=lambda x: len(x))
        return candidate

    def find_minimal_distance(self, src, tgt):
        paths = nx.all_simple_paths(self.g, src.id, tgt.id)
        distance = sorted(paths, key=lambda x: len(x))
        if len(distance) == 0:
            return 100000
        else:
            return len(distance[0])

    def __find_path_between_state(self, src, tgt):
        paths = nx.all_simple_paths(self.g, src.id, tgt.id)
        paths = list(paths)
        str_of_paths = set()
        paths_ = []
        for path in paths:
            key = ''.join(path)
            if key not in str_of_paths:
                str_of_paths.add(key)
                paths_.append(path)
        paths = sorted(paths_, key=lambda x: len(x))
        candidate = []
        for path in paths[:5]:
            p = []
            for i in range(len(path) - 1):
                n1 = path[i]
                n2 = path[i + 1]
                # priority Touch/LongTouch -> SetText -> KeyEvent -> intent
                candidate_edge = None
                for j in range(self.g.number_of_edges(n1, n2)):
                    edge = self.g.edges[(n1, n2, j)]['edge']
                    if candidate_edge is not None:
                        candidate_edge = Edge.compare_priority_and_return_higher(candidate_edge, edge)
                    else:
                        candidate_edge = edge
                if candidate_edge.priority >= Edge.MAX_PRIORITY:
                    p = None
                    break
                p.append(candidate_edge.to_event_data())
            if p is None:
                continue
            else:
                candidate.append(p)
        return candidate

    def __find_state_subset(self, src):
        result = []
        src_views = src.views
        src_widget_set = set(map(lambda widget: self.__widget_to_str(widget),
                                 filter(lambda widget: 'Layout' not in widget['class'], src_views)
                                 )
                             )
        for state in self.states.values():
            state_views = copy.deepcopy(state.views)
            state_views = filter(lambda widget: 'Layout' not in widget['class'] and 'TextView' not in widget['class'],
                                 state_views)
            state_views = map(lambda widget: self.__widget_to_str(widget), state_views)
            state_views = filter(lambda widget: 'android:id' not in widget, state_views)
            state_widget_set = set(state_views)
            if state_widget_set.issubset(src_widget_set) and state.id != src.id:
                result.append(state)
        return result

    def __find_same_activity_state(self, src):
        return list(filter(lambda state: state.activity == src.activity, self.states.values()))

    @staticmethod
    def __widget_to_str(widget):
        rid = ''
        text = ''
        content_desc = ''
        if 'resource-id' in widget:
            rid = widget['resource-id']
        if 'resource_id' in widget:
            rid = widget['resource_id']
        if 'text' in widget:
            text = widget['text']
        if 'content-desc' in widget:
            content_desc = widget['content-desc']
        if 'content_description' in widget:
            content_desc = widget['content_description']

        def empty_or_other(s):
            return s if s is not None else ''

        rid = '[resource-id]' + empty_or_other(rid)
        text = '[text]' + empty_or_other(text)
        content_desc = '[content-desc]' + empty_or_other(content_desc)
        return rid + text + content_desc

    # need test
    # need fix about meet a new state
    def add_edge(self, src, tgt, event):
        assert src['activity'], tgt['activity']
        assert src['gui'], tgt['gui']
        assert type(event) == gendroid.event.Event
        src_state, _ = self.get_most_closest_state(src)
        if src_state is None or _ < 0.2:
            src_state = self.add_node(src)
        tgt_state, _ = self.get_most_closest_state(tgt)
        if tgt_state is None or _ < 0.2:
            tgt_state = self.add_node(tgt)
        # src_state = self.create_state(src)
        # tgt_state = self.create_state(tgt)
        #
        # def get_or_add_state(state):
        #     if state.id in self.states:
        #         return self.states[state.id]
        #     else:
        #         self.states[state.id] = state
        #         self.g.add_node(state.id)
        #         return state
        #
        # src_state = get_or_add_state(src_state)
        # tgt_state = get_or_add_state(tgt_state)

        if self.__have_path_between_state(src_state, tgt_state):
            return
        fsm_log.info(f'add edge between {src_state.id} {tgt_state.id} {event.event_str()}')
        for i in range(self.g.number_of_edges(src_state.id, tgt_state.id)):
            edge = self.g.edges[(src_state.id, tgt_state.id, i)]['edge']
            # TODO static and dynamic will duplicated.
            # if edge.edge_type == Edge.STATIC:
            #     widget = edge.event['view']
            #     event_type = edge.event_type
            if edge.edge_type == Edge.DYNAMIC:
                selector = edge.event.selector
                action = edge.event_type
                if action == event.action:
                    try:
                        for key in selector:
                            if selector[key] != event.selector[key]:
                                continue
                    except TypeError or KeyError:
                        print(event)
                        print(edge.event)
                        return None
                    return edge
        dic = {
            'event': event,
            'event_type': event.action,
            'type': Edge.DYNAMIC,
            'start_state': src_state.id,
            'stop_state': tgt_state.id,
            'event_str': src_state.id + tgt_state.id + event.event_str()
        }
        new_edge = Edge(dic)
        self.edges[new_edge.event_str] = new_edge
        self.g.add_edge(src_state.id, tgt_state.id, edge=new_edge)
        return new_edge

    # need test
    def add_node(self, app_info):
        # _, score = self.get_most_closest_state(app_info)
        # if score >= 0.90:
        #     return _
        new_state = self.create_state(app_info)
        if new_state.id in self.states:
            return self.states[new_state.id]
        else:
            self.states[new_state.id] = new_state
            self.g.add_node(new_state.id)
            return new_state

    @staticmethod
    def hierarchical_to_list(gui, package):
        import xml.etree.ElementTree as et
        views = []
        root = et.fromstring(gui)
        for view in root.iter():
            if view.get('package') == package:
                views.append(view.attrib)
        return views

    @staticmethod
    def get_all_leaf_node(gui, package):
        import xml.etree.ElementTree as et
        views = []
        root = et.fromstring(gui)

        def iteration(root):
            if len(root) != 0:
                for child in list(root):
                    iteration(child)
                # iteration(list(root))
            else:
                if root.get('package') == package:
                    views.append(root.attrib)

        # for view in root.iter():
        # if view.get('package') == package:
        # views.append(view.attrib)
        iteration(root)
        return views

    def create_state(self, app_info):
        assert app_info['activity']
        assert app_info['gui']
        views = self.hierarchical_to_list(app_info['gui'], app_info['package'])
        activity = app_info['activity'][:len(app_info['package'])] + '/' + \
                   app_info['activity'][len(app_info['package']):]
        dic = {'foreground_activity': activity, 'views': views, 'type': State.DYNAMIC}
        new_state = State(dic)
        return new_state

    def get_temp_state_id(self, app_info):
        state = self.create_state(app_info)
        return state.id

    # Have tested
    def get_most_closest_state(self, app_info):
        new_state = self.create_state(app_info)
        if new_state.id in self.states:
            return self.states[new_state.id], 100
        views = self.get_all_leaf_node(app_info['gui'], app_info['package'])
        if app_info['package'] in app_info['activity']:
            activity = app_info['activity'][:len(app_info['package'])] + '/' + \
                       app_info['activity'][len(app_info['package']):]
        else:
            activity = app_info['package'] + '/' + app_info['activity']
        match = -1
        candidate_state = None
        l = []
        for state in self.states.values():
            if state.activity == activity:
                # print(state.id)
                import copy
                views_ = list(copy.deepcopy(state.views))
                # for widget in views, for widget_ in views_
                # only compare resource-id
                count = 0
                total = 0
                for widget in views:
                    if 'Layout' in widget.get('class') or 'Recycler' in widget.get(
                            'class') or 'ViewGroup' in widget.get('class') or 'Image' in widget.get('class'):
                        continue
                    total += 1
                    for widget_ in views_:
                        rid1 = widget.get('resource-id')
                        text1 = widget.get('text')
                        text2 = widget_['text']
                        content1 = widget.get('content-desc')
                        if state.type == state.STATIC:
                            rid2 = widget_['resource_id']
                            content2 = widget_['content_description']
                        else:
                            rid2 = widget_['resource-id']
                            content2 = widget_['content-desc']
                        if self.equal_or_both_null(rid1, rid2) and self.equal_or_both_null(text1, text2) \
                                and self.equal_or_both_null(content1, content2):
                            count += 1
                            l.append(widget_)
                            views_.remove(widget_)
                            break
                if count / total > match:
                    candidate_state = state
                    match = count / total
        if candidate_state is None:
            return None, 0
        return candidate_state, match

    @staticmethod
    def equal_or_both_null(a, b):
        bool_a = a != '' and a is not None
        bool_b = b != '' and b is not None
        if bool_a and bool_b:
            return a == b
        if not bool_a and not bool_b:
            return True
        return False

    @staticmethod
    def safe_equal(a, b):
        bool_a = a != '' and a is not None
        bool_b = b != '' and b is not None
        if bool_a and bool_b:
            return a == b

    # Have tested
    # resource_id don't have package information
    # when resource-id's prefix is 'android:id', it lack identification degree
    def get_states_contain_widget(self, widget: dict):
        resource_id = str(widget['resource-id'])
        candidate_target_states = []
        for state in self.states.values():
            if state.type == State.STATIC:
                rid_key = 'resource_id'
                content = 'content_description'
            else:
                rid_key = 'resource-id'
                content = 'content-desc'
            text = 'text'
            for widget_ in state.views:
                if widget_[rid_key] is None or len(widget_[rid_key]) == 0:
                    continue
                else:
                    widget_rid = str(widget_[rid_key])
                    if resource_id.startswith('android:id'):
                        if (widget['content-desc'] is not None and widget_[content] == widget['content-desc']) \
                                or (widget['text'] is not None and widget_[text] == widget['text']):
                            candidate_target_states.append(state)
                            break
                    elif widget_rid == resource_id:
                        candidate_target_states.append(state)
                        break
        return candidate_target_states

    def have_path_between_device_info(self, pre_info, post_info):
        src, _ = self.get_most_closest_state(pre_info)
        if src is None:
            return False
        tgt, _ = self.get_most_closest_state(post_info)
        if tgt is None:
            return False
        return self.__have_path_between_state(src, tgt)

    def __have_path_between_state(self, src, tgt):
        return nx.has_path(self.g, src.id, tgt.id)

    def __have_out_edge(self, state):
        for edge in self.edges.values():
            if edge.src == state.id:
                return True
        return False

    def widgets(self):
        keys = set()
        widgets = []
        dynamic_keys = [
            'resource-id', 'content-desc', 'text', 'class'
        ]
        static_keys = [
            'resource_id', 'content_description', 'text', 'class'
        ]
        final_keys = dynamic_keys
        for state in self.states.values():
            # paths = self.__find_path_between_state(src.id, state.id)
            for widget in state.views:
                selector = {}
                selector_key = ''
                key_set = None
                if state.type == State.DYNAMIC:
                    key_set = dynamic_keys
                if state.type == State.STATIC:
                    key_set = static_keys
                for index, key in enumerate(key_set):
                    selector[final_keys[index]] = widget[key]
                    selector_key += widget[key] if widget[key] else 'None'
                if selector_key not in keys:
                    # widgets.append([state.id, selector])
                    widgets.append(selector)
                    keys.add(selector_key)
        return widgets

    def widgets_with_distance(self, app_current):
        src, _ = self.get_most_closest_state(app_current)
        keys = set()
        widgets = []
        dynamic_keys = [
            'resource-id', 'content-desc', 'text', 'class'
        ]
        static_keys = [
            'resource_id', 'content_description', 'text', 'class'
        ]
        final_keys = dynamic_keys
        for state in self.states.values():
            distance = self.find_minimal_distance(src, state)
            for widget in state.views:
                selector = {}
                selector_key = ''
                key_set = None
                if state.type == State.DYNAMIC:
                    key_set = dynamic_keys
                if state.type == State.STATIC:
                    key_set = static_keys
                for index, key in enumerate(key_set):
                    selector[final_keys[index]] = widget[key]
                    selector_key += widget[key] if widget[key] else 'None'
                    # widgets.append([state.id, selector])
                widgets.append([selector, distance])
        return widgets


class State:
    STATIC = 's'
    DYNAMIC = 'd'

    def __init__(self, dic):
        self.type = dic['type']
        self.activity = dic['foreground_activity']
        self.views = dic['views']
        # self.id = dic['state_str']
        if 'state_str' in dic:
            self.id = dic['state_str']
        else:
            self.id = self.__get_state_str()

    def __eq__(self, other):
        return self.id == other.id

    def __get_state_str(self):
        def md5(input_str):
            import hashlib
            return hashlib.md5(input_str.encode('utf-8')).hexdigest()

        state_str_raw = self.__get_state_str_raw()
        return md5(state_str_raw)

    def __get_state_str_raw(self):
        view_signatures = set()
        for view in self.views:
            view_signature = self.__get_view_signature(view)
            if view_signature:
                view_signatures.add(view_signature)
        return "%s{%s}" % (self.activity, ",".join(sorted(view_signatures)))

    @staticmethod
    def __get_view_signature(view_dict):
        """
        get the signature of the given view
        @param view_dict: dict, an element of list DeviceState.views
        @return:
        """
        if 'signature' in view_dict:
            return view_dict['signature']

        view_text = State.__safe_dict_get(view_dict, 'text', "None")
        if view_text is None or len(view_text) > 50:
            view_text = "None"
        signature = "[class]%s[resource_id]%s[text]%s[%s,%s,%s]" % \
                    (State.__safe_dict_get(view_dict, 'class', "None"),
                     State.__safe_dict_get(view_dict, 'resource-id', "None"),
                     view_text,
                     State.__key_if_true(view_dict, 'enabled'),
                     State.__key_if_true(view_dict, 'checked'),
                     State.__key_if_true(view_dict, 'selected'))
        view_dict['signature'] = signature
        return signature

    @staticmethod
    def __safe_dict_get(d, key, default_value):
        return d[key] if key in d else default_value

    @staticmethod
    def __key_if_true(view_dict, key):
        return key if (key in view_dict and view_dict[key]) else ""


class Edge:
    STATIC = 's'
    DYNAMIC = 'd'
    STATIC_ACTION_TYPE = ['touch', 'long_touch', 'set_text', 'key', 'intent', 'swipe', 'scroll', 'kill_app']
    DYNAMIC_ACTION_TYPE = ['click', 'long_click', 'set_text',
                           'home',
                           'back',
                           'left',
                           'right',
                           'up',
                           'down',
                           'center',
                           'menu',
                           'volume_up',
                           'volume_down',
                           'volume_mute',
                           'power']
    D_S_MAP = bidict({'click': 'touch', 'long_click': 'long_touch', 'set_text': 'set_text',
                      'swipe': 'swipe', 'scroll': 'scroll'})
    MAX_PRIORITY = STATIC_ACTION_TYPE.index('kill_app')

    def __init__(self, dic):
        self.edge_type = dic['type']
        self.event = dic['event']
        if self.edge_type == Edge.STATIC:
            self.event_type = self.event['event_type']
        if self.edge_type == Edge.DYNAMIC:
            self.event_type = self.event.action
        self.priority = self.get_priority()
        self.src = dic['start_state']
        self.tgt = dic['stop_state']
        self.event_str = dic['event_str']

    def get_priority(self):
        if self.edge_type == Edge.STATIC:
            return Edge.STATIC_ACTION_TYPE.index(self.event_type)
        if self.edge_type == Edge.DYNAMIC:
            return Edge.DYNAMIC_ACTION_TYPE.index(self.event_type)

    def __eq__(self, other):
        if type(other) == Edge:
            # TODO
            pass
        else:
            return False

    def to_event_data(self):
        if self.edge_type == Edge.STATIC:
            S_D_MAP = Edge.D_S_MAP.inverse
            if self.event_type == 'key':
                action = self.event['name'].lower()
                return EventData(action=action, selector=None, data=None)
            else:
                if self.event_type in S_D_MAP:
                    action = S_D_MAP[self.event_type]
                else:
                    action = self.event_type
                if action == 'intent':
                    return EventData(action=action, selector=None, data={'intent': self.event['intent']})
                if action == 'scroll':
                    return EventData(action=action, selector=None, data={'direction': self.event['direction']})
                import copy
                view = copy.deepcopy(self.event['view'])
                view['resource-id'] = view['resource_id']
                view['content-desc'] = view['content_description']
                # action = S_D_MAP[self.event_type]
                data = None
                if action == 'set_text':
                    data = {'text': self.event['text']}
                # if action == 'click':
                #     if view['resource-id'] is None and view['content-desc'] is None:
                #         return EventData(action='click_with_pos', selector=view, data={'position': view['bounds']})
                return EventData(action=action, selector=view, data=data)
        else:
            if self.event_type == 'set_text':
                data = {'text': self.event.text}
                return EventData(action=self.event_type, selector=self.event.selector, data=data)
            else:
                return EventData(action=self.event_type, selector=self.event.selector, data=None)

    @staticmethod
    def compare_priority_and_return_higher(e1, e2):
        if e1.edge_type == e2.edge_type:
            return e1 if e1.priority <= e2.priority else e2
        if e1.edge_type != e2.edge_type:
            if e1.edge_type == Edge.DYNAMIC:
                return e1
            else:
                return e2


if __name__ == '__main__':
    f = FSM('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/gmail/output')
    s = f.states['3adebc8dc54482b9771e734d84ec1a72']
    print(f.find_minimal_distance(f.states['6d72da7106ec9be4919540b4f0806429'],
                                  f.states['864b9d369a581ca424778f259b6767bf']))
    # ws = f.widgets()
    # for w in ws:
    #     print(w)
    # for i in range(len(s1)):
    #     if s1[i] != s2[i]:
    #         print(s1[i], s2[i])

    # print(len(v1), len(v2))
    # s1 = '\n'.join([widget['signature'] for widget in v1])
    # for widget in v1:
    # print(widget['signature'])

    # s2 = ''
    # s2 = '\n'.join([widget['signature'] for widget in v1])
    # for widget in v2:
    #     print(widget['signature'])

    # def widget_to_str(widget):
    #     rid = ''
    #     text = ''
    #     content_desc = ''
    #     if 'resource-id' in widget:
    #         rid = widget['resource-id']
    #     if 'resource_id' in widget:
    #         rid = widget['resource_id']
    #     if 'text' in widget:
    #         text = widget['text']
    #     if 'content-desc' in widget:
    #         content_desc = widget['content-desc']
    #     if 'content_description' in widget:
    #         content_desc = widget['content_description']
    #
    #     def empty_or_other(s):
    #         return s if s is not None else ''
    #
    #     rid = '[resource-id]' + empty_or_other(rid)
    #     text = '[text]' + empty_or_other(text)
    #     content_desc = '[content-desc]' + empty_or_other(content_desc)
    #     return rid + text + content_desc

    # state_views = s.views
    # state_views = list(
    #     filter(lambda widget: 'Layout' not in widget['class'] and 'TextView' not in widget['class'], state_views))
    # state_views = list(map(lambda widget: widget_to_str(widget), state_views))
    # state_views = list(filter(lambda widget: 'android:id' not in widget, state_views))
    # state_widget_set = set(state_views)
    # state_widget_set = set(map(lambda widget: widget_to_str(widget),
    #                            filter(lambda widget: 'Layout' not in widget['class'], state_views)
    #                            )
    #                        )
    # for i in state_widget_set:
    #     print(i)
    # edges = f.edges.values()
    # intent_edge = None
    # for e in edges:
    #     print(e.to_event_data())
    # assert intent_edge
    # print(intent_edge.to_event_data())
