from demo.record import Record


class Series:
    def __init__(self, record_list):
        self.series = []
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
