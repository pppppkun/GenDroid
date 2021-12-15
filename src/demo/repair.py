"""
this class will give confidence between query and given node
"""
from demo.series import Series
from demo.device import Device


class Repair:
    def __init__(self, strategy):
        self.strategy = strategy
        pass

    def select(self, gui, record):
        return record.event

    def construct_event_series(self, device: Device, record_series):
        pass

    def combine_select(self, es1, es2):
        pass

    # need a return format
    def recovery(self, series: Series, device: Device, record_index):
        if self.strategy == 'try_next':
            return series[record_index + 1]
        elif self.strategy == 'ERROR_RECOVERY':
            record_series = series.get_direct_record_series(record_index)
            relate_index = series.get_relate_index(record_index)
            device.stop_and_restart(series.get_before_record_series(record_index))
            # the line below is error, need to execute the all repair event in executor.
            _, _ = device.execute([record.event for record in record_index[: relate_index - 1]])
            # first: try to repair the last event
            # second: try to repair the whole event_series
            gui = device.get_ui_info()
            events = self.select(gui, series[record_index - 1])
            for event in events:
                device.execute(event)
                _, result = device.execute(series[record_index].event)
                if result:
                    return [event], series[record_index].event
            # TODO whether to search?
            device.stop_and_restart(series.get_before_record_series(record_index))
            events = self.construct_event_series(device, record_series)
            for event in events:
                device.execute(event)
            return events
