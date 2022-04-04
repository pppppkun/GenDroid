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
    def execute(self, ves):
        for i in range(len(ves) - 1):
            src_des = ves[i].description
            tgt_des = ves[i + 1].description
            src_widget = self.analyst.dynamic_match_widget(src_des)
            src_event = self.constructor.generate_events_from_widget(widget=src_widget, action=None, data=ves[i].data)
            self.device.execute(src_event)
            tgt_widgets = self.analyst.static_match_activity(tgt_des)
            for tgt_widget in tgt_widgets:
                path = self.analyst.calculate_path_between_activity(src_des, tgt_widget)
                if path is not None:
                    events = path[0]
                    self.device.execute(events)
                    # events = self.constructor.generate_events_from_widget(path)
                    # self.device.execute(events)
                    break

    def record(self, events):
        for event in events:
            self.device.execute(event)
