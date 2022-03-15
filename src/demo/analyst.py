import logging
import os.path
import pydot
import networkx as nx
import demo.db as db
import demo.utils as utils
from demo.call_graph_parser import CallGraphParser
from collections import defaultdict
import xml.etree.ElementTree as et

analyst_log = logging.getLogger('analyst')
analyst_log.setLevel(logging.DEBUG)
analyst_log_ch = logging.StreamHandler()
analyst_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
analyst_log_ch.setFormatter(formatter)
analyst_log.addHandler(analyst_log_ch)

widget_attempt_action_map = {
    'ImageView': ['click'],
    'EditText': ['set_text'],
    'TextView': ['click'],
    'Button': ['click'],
    'ImageButton': ['click'],
    'CheckBox': ['click']
}


class Analyst:
    def __init__(self, device, threshold, static_info_folder):
        self.device = device
        self.threshold = threshold
        self.static_info_folder = static_info_folder
        self.cgp = CallGraphParser(static_info_folder)

    def check_reachability(self, w, current_activity):
        act_from = self.device.package + current_activity
        act_to = w['package'] + current_activity
        potential_paths = self.cgp.get_paths_between_activities(act_from, act_to, consider_naf_only_widget=False)
        if w['activity'] == current_activity:
            potential_paths.insert(0, [])
        for path in potential_paths:
            match = True
            if match:
                return match
        return None

    def validate_path(self, path, w_target, invalid_paths):
        pass
        # path_show = []
        # for node in path:
        #     if '(' in node:  # a GUI event
        #         if node.startswith('D@'):
        #             gui = ' '.join(node.split()[:-1])
        #         else:
        #             gui = self.rp.get_wName_from_oId(node.split()[0])
        #         path_show.append(gui)
        #     else:
        #         path_show.append(utils.get_activity((node)))
        # print(f'Validating path: ', path_show)
        #
        # # prune verified wrong path
        # for ip in invalid_paths:
        #     if ip == path[:len(ip)]:
        #         print('Known invalid path prefix:', path[:len(ip)])
        #         return None
        #
        # # start follow the path to w_target
        # _, __, ___ = self.execute_target_events([])
        # stepping = []
        # for i, node in enumerate(path):
        #     if '(' in node:  # a GUI event
        #         w_id = ' '.join(node.split()[:-1])
        #         action = node.split('(')[1][:-1]
        #         action = 'long_press' if action in ['onItemLongClick', 'onLongClick'] else 'click'
        #         if w_id.startswith('D@'):  # from dynamic exploration
        #             # e.g., 'D@class=android.widget.Button&resource-id=org.secuso.privacyfriendlytodolist:id/btn_skip&text=Skip&content-desc='
        #             kv_pairs = w_id[2:].split('&')
        #             kv = [kvp.split('=') for kvp in kv_pairs]
        #             criteria = {k: v for k, v in kv}
        #             print('D@criteria:', criteria)
        #             w_stepping = WidgetUtil.locate_widget(self.runner.get_page_source(), criteria)
        #         else:  # from static analysis
        #             w_name = self.rp.get_wName_from_oId(w_id)
        #             w_stepping = WidgetUtil.locate_widget(self.runner.get_page_source(), {'resource-id': w_name})
        #         if not w_stepping:
        #             # add current path prefix to invalide path
        #             is_existed = False
        #             for ip in invalid_paths:
        #                 if ip == path[:i + 1]:
        #                     is_existed = True
        #             if not is_existed:
        #                 invalid_paths.append([h for h in path[:i + 1]])
        #             return None
        #         w_stepping['action'] = [action]
        #         w_stepping['activity'] = self.runner.get_current_activity()
        #         w_stepping['package'] = self.runner.get_current_package()
        #         w_stepping['event_type'] = 'stepping'
        #         stepping.append(w_stepping)
        #         act_from = self.runner.get_current_package() + self.runner.get_current_activity()
        #         self.runner.perform_actions([stepping[-1]], require_wait=False, reset=False, cgp=self.cgp)
        #         self.cache_seen_widgets(self.runner.get_page_source(),
        #                                 self.runner.get_current_package(),
        #                                 self.runner.get_current_activity())
        #         act_to = self.runner.get_current_package() + self.runner.get_current_activity()
        #         self.cgp.add_edge(act_from, act_to, w_stepping)
        #
        # # check if the target widget exists
        # # if self.runner.get_current_activity() not in ppath[-1]:
        # #     return None
        # attrs_to_check = set(WidgetUtil.FEATURE_KEYS).difference({'clickable', 'password'})
        # criteria = {k: w_target[k] for k in attrs_to_check if k in w_target}
        # # for text_presence oracle, force the text to be the same as the src_event
        # if self.src_events[self.current_src_index]['action'][0] == 'wait_until_text_presence':
        #     criteria['text'] = self.src_events[self.current_src_index]['action'][3]
        # # for confirm email: if both prev and current src_action are input email
        # if self.current_src_index > 0 and self.is_for_email_or_pwd(self.src_events[self.current_src_index-1],
        #                                                            self.src_events[self.current_src_index]):
        #     # for the case of matching to the only one email field
        #     if StrUtil.is_contain_email(self.src_events[self.current_src_index]['action'][1]):
        #         criteria['text'] = self.runner.databank.get_temp_email(renew=False)
        # w_tgt = WidgetUtil.locate_widget(self.runner.get_page_source(), criteria)
        # if not w_tgt:
        #     return None
        # else:
        #     src_event = self.src_events[self.current_src_index]
        #     w_tgt['stepping_events'] = stepping
        #     w_tgt['package'] = self.runner.get_current_package()
        #     w_tgt['activity'] = self.runner.get_current_activity()
        #     w_tgt['event_type'] = src_event['event_type']
        #     w_tgt['score'] = WidgetUtil.weighted_sim(w_tgt, src_event)
        #     if src_event['action'][0] == 'wait_until_text_invisible':
        #         # here, w_tgt is the nearest button to the text. Convert it to the oracle event
        #         for k in w_tgt.keys():
        #             if k not in ['stepping_events', 'package', 'activity', 'event_type', 'score']:
        #                 w_tgt[k] = ''
        #
        #     if src_event['action'][0] == 'wait_until_text_presence':
        #         # cache the closest button on the current screen for possible text_invisible oracle in the future
        #         self.nearest_button_to_text = WidgetUtil.get_nearest_button(self.runner.get_page_source(), w_tgt)
        #         self.nearest_button_to_text['activity'] = w_tgt['package']
        #         self.nearest_button_to_text['package'] = w_tgt['activity']
        #
        #     return w_tgt

    def action_analysis(self, widget):
        events = db.get_all_events()
        for event in events:
            r = utils.is_same_widget_from_widget_info(widget, event.widget)
            if r:
                return event.action

        d = dict()
        for event in events:
            class_ = utils.get_class(event.widget)
            d.setdefault(class_, dict())
            d[class_].setdefault(event.action, 0)
            d[class_][event.action] += 1

        class_ = utils.get_class(widget)
        if class_ in d:
            actions = d[class_]
            action = max(zip(actions.values(), actions.keys()))[0]
            return action

        return widget_attempt_action_map[class_]

    # static analysis to get action is better!
    def analysis(self, apk):
        pass
