from atm.analyst import Analyst
from atm.construct import Constructor
from atm.device import Device


class Executor:
    def __init__(self, analyst: Analyst, constructor: Constructor, device: Device):
        self.analyst = analyst
        self.constructor = constructor
        self.device = device
        pass

    # 1. get widget dynamic and static.
    # 2. calculate similarity between source and d and get widget w1
    # 3. calculate similarity between destination and s and get widget w2
    # 4. calculate paths from activity[after execute w1] to activity[which has w2]
    # widgets = get_all_widgets()
    # calculated similarity between <widgets source>, <widgets destination>
    def execute(self, descriptions):
        for i in range(len(descriptions) - 1):
            src_des = descriptions[i]
            tgt_des = descriptions[i + 1]
            src_widget = self.analyst.dynamic_match_widget(src_des)[0]
            src_event = self.constructor.generate_events(src_widget)
            self.device.execute(src_event)
            src_act = self.device.activity()
            tgt_widgets = self.analyst.static_match_activity(tgt_des)
            for tgt_widget in tgt_widgets:
                path = self.analyst.calculate_path_between_activity(src_act, tgt_widget.activity, tgt_des, tgt_widget)
                if path is not None:
                    events = self.constructor.generate_events(path)
                    self.device.execute(events)
                    break

    def record(self, events):
        for event in events:
            self.device.execute(event)
