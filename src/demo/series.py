from demo.record import Record


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


class Series:
    def __init__(self, record_list=None):
        self.series = []
        if record_list:
            self.init_series(record_list)

    def __len__(self):
        return len(self.series)

    def __getitem__(self, item):
        return self.series[item]

    def init_series(self, record_list):
        for record in record_list:
            self.series.append(Record(record))

    def get_direct_record_series(self, record_index):
        result = []
        es = self.series[record_index].event_series
        for record in self.series:
            if es == record.event_series:
                result.append(record)
        return result

    def get_before_record_series(self, record_index):
        result = []
        es = self.series[record_index].event_series
        for record in self.series:
            if es == record.event_series:
                break
            else:
                result.append(record)
        return result

    def get_relate_index(self, record_index):
        record_series = self.get_direct_record_series(record_index)
        for i in range(len(record_series)):
            if self.series[record_index] == record_series[i]:
                return i
        return -1
