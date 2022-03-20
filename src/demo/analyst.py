import logging
import demo.db as db
import demo.utils as utils
from demo.event import event_factory
from demo.call_graph_parser import CallGraphParser

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

    def check_reachability(self, w, current_activity, executor):
        act_from = self.device.package + current_activity
        act_to = w['package'] + current_activity
        potential_paths = self.cgp.get_paths_between_activities(act_from, act_to, consider_naf_only_widget=False)
        if w['activity'] == current_activity:
            potential_paths.insert(0, [])
        invalid_paths = []
        for path in potential_paths:
            match = self.validate_path(path, w, invalid_paths, executor)
            if match:
                return match
        return None

    def validate_path(self, path, w_target, invalid_paths, executor):
        for ip in invalid_paths:
            if ip == path[:len(ip)]:
                analyst_log.log('known invalid path prefix: ' + path[:len(ip)])
        path_show = []
        for node in path:
            if '(' in node:
                if node.startswith('D@'):
                    # D@[attrib=value] action
                    gui = ' '.join(node.split()[:-1])
                else:
                    # ${ID} (${ACTION})
                    gui = db.get_widget_name_from_id(node.split()[0])
                path_show.append(gui)
            else:
                path_show.append(utils.get_activity(node))
        stepping = []
        for index, node in enumerate(path):
            if '(' in node:
                if node.startswith('D@'):
                    # D@a=b&c=e ${action}
                    # k_v -> a = b
                    action = node.split()[1]
                    criteria = dict(
                        map(lambda k_v: (k_v.split('=')[0], k_v.split('=')[1]), node.split()[0][2:].split('&')))
                    analyst_log.log('D@criteria: ' + criteria.__str__())
                    widget = self.device.select_widget(utils.get_selector_from_dynamic_edge(criteria))
                else:
                    # resource-id actually
                    action = node.split('(')[1][:-1]
                    widget_name = db.get_widget_name_from_id(node.split()[0])
                    widget = self.device.select_widget({'resource-id': widget_name})
                if not widget:
                    if path[:index + 1] not in invalid_paths:
                        invalid_paths.append(path[: index + 1])
                    return None
                # TODO
                pre_info = self.device.app_current()
                if 'Long' in action or 'long' in action:
                    widget.long_click()
                else:
                    widget.click()
                post_info = self.device.app_current()
                # 2. cache seen widgets
                # 3. add edge (need to add an abstract)
                stepping.append(widget)
                self.cache_seen_widgets()
                self.cgp.add_edge(pre_info['package'] + pre_info['activity'],
                                  post_info['package'] + post_info['activity'], widget)
        # check target widget exists
        if self.device.exists_widget(w_target):
            w_tgt = self.device.select_widget(w_target)
            # cache_nearest_button_to_text
            return w_tgt
        else:
            return False
        return True

    def cache_seen_widgets(self):
        pass

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
