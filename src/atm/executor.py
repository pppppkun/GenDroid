class Executor:
    def __init__(self, analyst, constructor, device):
        self.analyst = analyst
        self.constructor = constructor
        self.device = device
        pass

    def execute(self, v_events):
        for i in range(len(v_events) - 1):
            source = v_events[i]
            destination = v_events[i + 1]
            source_widgets = self.analyst.dynamic_match_widget(source)
            destination_activity = self.analyst.static_match_activity(destination)
            path = self.analyst.calculate_path_between_activity('this', destination_activity, source)
            events = self.constructor.generate_events(source_widgets)
            source.events = events
            source.index = 0
            self.device.execute(events[source.index])
            self.device.execute(path)
            # 1. get widget dynamic and static.
            # 2. calculate similarity between source and d and get widget w1
            # 3. calculate similarity between destination and s and get widget w2
            # 4. calculate paths from activity[after execute w1] to activity[which has w2]
            # widgets = get_all_widgets()
            # calculated similarity between <widgets source>, <widgets destination>
            #
