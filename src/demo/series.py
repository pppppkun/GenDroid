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
