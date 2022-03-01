class EventSeries:
    def __init__(self):
        self.series = []

    def __len__(self):
        return len(self.series)

    def __getitem__(self, item):
        if isinstance(item, slice):
            start, stop, step = item.indices(len(self.series))
            index_list = list(range(start, stop, step))
            temp = []
            for i in index_list:
                temp.append(self.series[i])
            return temp
        else:
            return self.series[item]

    def __setitem__(self, key, value):
        self.series[key] = value

    def get_events_expect_last(self):
        events = self.get_events()
        if len(events) == 1:
            return events
        else:
            return events[:-1]

    def get_events(self):
        events = []
        for event in self.series:
            if isinstance(event, list):
                events.append(event[1])
            else:
                events.append(event)
        return events

    def is_event(self, item):
        if type(self.series[item]) is list:
            return False
        else:
            return True

    def last_item_type(self):
        return type(self.series[len(self.series) - 1])

    def append(self, item):
        self.series.append(item)
        return self
