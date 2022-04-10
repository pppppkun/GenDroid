import atm.event
from atm.event import build_event, EventData
from bidict import bidict
from atm.widget import Widget
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
                # print(event)
            event['type'] = Edge.STATIC
            edge = Edge(event)
            self.g.add_edge(edge.src, edge.tgt, edge=edge)
            self.edges[edge.event_str] = edge
        pass

    def find_path_to_target_widget(self, device, target_widget: dict):
        try:
            src, _ = self.get_most_closest_state(device.app_current_with_gui())
            tgts = self.get_states_contain_widget(target_widget['resource-id'])
        except:
            fsm_log.error('error to find state.')
            return []
        fsm_log.info(f'begin to find path between {src.id} {target_widget["resource-id"]}')
        candidate = []
        for tgt in tgts:
            candidate += self.__find_path_between_state(src, tgt)
        return candidate

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
                # priority Touch/LongTouch -> SetText -> Scroll
                candidate_edge = None
                for j in range(self.g.number_of_edges(n1, n2)):
                    edge = self.g.edges[(n1, n2, j)]['edge']
                    if candidate_edge is not None:
                        candidate_edge = Edge.compare_priority_and_return_higher(candidate_edge, edge)
                    else:
                        candidate_edge = edge
                assert candidate_edge is not None
                p.append(candidate_edge.to_event_data())
            candidate.append(p)
        return candidate

    # need test
    # need fix about meet a new state
    def add_edge(self, src, tgt, event):
        assert src['activity'], tgt['activity']
        assert src['gui'], tgt['gui']
        assert type(event) == atm.event.Event
        src_state, _ = self.get_most_closest_state(src)
        tgt_state, score = self.get_most_closest_state(tgt)
        if score < 0.9:
            tgt_state = self.add_node(tgt)
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

    def create_state(self, app_info):
        assert app_info['activity']
        assert app_info['gui']
        views = self.hierarchical_to_list(app_info['gui'], app_info['package'])
        activity = app_info['activity'][:len(app_info['package'])] + '/' + \
                   app_info['activity'][len(app_info['package']):]
        dic = {'foreground_activity': activity, 'views': views, 'type': State.DYNAMIC}
        new_state = State(dic)
        return new_state

    # Have tested
    def get_most_closest_state(self, app_info):
        views = self.hierarchical_to_list(app_info['gui'], app_info['package'])
        if app_info['package'] in app_info['activity']:
            activity = app_info['activity'][:len(app_info['package'])] + '/' + \
                       app_info['activity'][len(app_info['package']):]
        else:
            activity = app_info['package'] + '/' + app_info['activity']
        match = -1
        candidate_state = None
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
                    if 'Layout' in widget.get('class'):
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
                            # print(widget.get('resource-id'), widget.get('text'))
                            # print(widget_['resource_id'], widget_['text'])
                            count += 1
                            views_.remove(widget_)
                            break
                if count / total > match:
                    candidate_state = state
                    # print(count / total, candidate_state.id)
                    match = count / total
        # assert candidate_state is not None
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

    # Have tested
    # resource_id don't have package information
    def get_states_contain_widget(self, resource_id):
        candidate_target_states = []
        for state in self.states.values():
            for widget_ in state.views:
                if state.type == State.STATIC:
                    rid_key = 'resource_id'
                else:
                    rid_key = 'resource-id'
                if widget_[rid_key] is None or len(widget_[rid_key]) == 0:
                    continue
                else:
                    widget_rid = str(widget_[rid_key])
                    if widget_rid == resource_id:
                        candidate_target_states.append(state)
                        break
        return candidate_target_states

    def have_path_between_device_info(self, pre_info, post_info):
        src, _ = self.get_most_closest_state(pre_info)
        tgt, _ = self.get_most_closest_state(post_info)
        return self.have_path_between_state(src, tgt)

    def have_path_between_state(self, src, tgt):
        paths = nx.all_simple_paths(self.g, src, tgt)
        return len(paths) != 0


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
                    widgets.append(selector)
                    keys.add(selector_key)

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
    STYPE = ['touch', 'long_touch', 'set_text', 'key', 'swipe', 'scroll', 'intent', 'kill_app']
    DTYPE = ['click', 'long_click', 'set_text',
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
    D_S_MAP = bidict({'click': 'touch', 'long_click': 'long_touch', 'set_text': 'set_text'})

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
            return Edge.STYPE.index(self.event_type)

    def __eq__(self, other):
        if type(other) == Edge:
            # TODO
            pass
        else:
            return False

    def to_event_data(self):
        # TODO
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
                import copy
                assert 'view' in self.event
                view = copy.deepcopy(self.event['view'])
                view['resource-id'] = view['resource_id']
                view['content-desc'] = view['content_description']
                # action = S_D_MAP[self.event_type]
                data = None
                if action == 'set_text':
                    data = {'text': self.event['text']}
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
    f = FSM('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/todo/output')
    widgets = f.widgets()
    for widget in widgets:
        print(widget)
    print(len(widgets))

    non_action_view = {
        'Layout',
        'Group',
        'Recycle',
        'Scroll',
        'SeekBar'
    }


    def filter_by_class(node):
        class_ = node['class']
        if class_ is None:
            return False
        result = True
        for view in non_action_view:
            if view in class_:
                result = False
                break
        return result


    widgets = list(filter(filter_by_class, widgets))
    print(len(widgets))

    # for edge in f.edges:
    #     e = f.edges[edge]
    #     print(e.event)
    # print(f.states[s].views)
    # start = 'dca53e74e20302aaaccdcec2bcf7ae65'
    # candidate = f.get_states_contain_widget('org.secuso.privacyfriendlytodolist:id/title')
    # for state in candidate:
    #     print(state.id)
    # import uiautomator2 as u2
    #
    # d = u2.connect()
    # app_current = d.app_current()
    # app_current['gui'] = d.dump_hierarchy()
    # state, _ = f.get_most_closest_state(app_current)
    # print(state.id)
