import logging
import demo.db as db
import demo.utils as utils

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
    def gui_analysis(self, gui):
        guis = db.get_all_guis()
        for gui in guis:
            rid, pre, _ = gui
            #

    def description_analysis(self, description):
        pass

    def event_analysis(self):
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


analyst = Analyst()
