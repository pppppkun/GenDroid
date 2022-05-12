from genDroid.widget import Widget
from genDroid.db import DataBase
from genDroid.event import build_event, event_factory
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

    def generate_events_from_widget(self, widget, action=None, data=None):
        clazz = widget.get_class()
        clazz = clazz[clazz.rindex('.') + 1:]
        candidate_action = None
        if action:
            candidate_action = action
        else:
            a = self.db.get_action_from_history(widget.to_selector())
            if a is not None:
                candidate_action = a
            else:
                if clazz in widget_attempt_action_map:
                    candidate_action = widget_attempt_action_map[clazz][0]
                else:
                    candidate_action = 'click'
        if data is not None:
            candidate_action = 'set_text'
        if candidate_action == 'set_text' and data is None:
            data = {'text': 'hello'}
        event = build_event(candidate_action, widget.to_selector(), data)
        return event

    def generate_event_from_node(self, node, action=None, data=None):
        widget = Widget(node.attrib)
        if 'AmountEditText' in widget.get_resource_id():
            data['text'] = '100'
        return self.generate_events_from_widget(widget, action, data)

    @staticmethod
    def generate_event_from_event_data(event_data):
        event = event_factory[event_data.action](event_data)
        return event
