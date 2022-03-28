from atm.widget import Widget
from atm.db import DataBase
from atm.event import build_event
import logging

construct_log = logging.getLogger('construct')
construct_log.setLevel(logging.DEBUG)
construct_log_ch = logging.StreamHandler()
construct_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
construct_log_ch.setFormatter(formatter)
construct_log.addHandler(construct_log_ch)

widget_attempt_action_map = {
    'ImageView': ['click'],
    'EditText': ['set_text'],
    'TextView': ['click'],
    'Button': ['click'],
    'ImageButton': ['click'],
    'CheckBox': ['click']
}


class Constructor:
    def __init__(self, db: DataBase):
        self.db = db
        pass

    def generate_events(self, widgets, action=None, data=None):
        work_list = []
        if type(widgets) == Widget:
            work_list.append(widgets)
        events = []
        for widget in work_list:
            clazz = widget.get_class()
            candidate_action = None
            if action:
                candidate_action = action
            else:
                a = self.db.get_action_from_history(widget.to_selector())
                if a != None:
                    candidate_action = a
                else:
                    if clazz in widget_attempt_action_map:
                        candidate_action = widget_attempt_action_map[clazz][0]
            event = build_event(candidate_action, widget.get_attribute(), data)
            events.append(event)
        return events
