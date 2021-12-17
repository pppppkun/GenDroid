"""
this class will give confidence between query and given node
"""
from demo.series import Series
from demo.device import Device
from functools import reduce
import xml.etree.ElementTree as et

# TODO fill the map
action_attrib_map = {
    'set_text': ['enable', 'focusable']
}


# TODO move checkpoint to local
def confidence(nodes, selector):
    pass


class Repair:
    def __init__(self, strategy):
        self.strategy = strategy
        pass

    @staticmethod
    def select(gui, record):
        root = et.fromstringlist(gui)
        nodes_with_confidence = \
            filter(
                lambda node: reduce(
                    lambda x, y: x and y,
                    map(
                        lambda x: node[x],
                        action_attrib_map[record.action]
                    )
                ),
                dict(
                    map(
                        lambda x: (x, confidence(x, record.selector)),
                        (node for node in root.iter())
                    )
                )
            )
        for node in nodes_with_confidence:
            yield node
        # need a filter
        # node = [node for node in root.iter() if record]

    def construct_event_series(self, device: Device, record_series):
        yield 1
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
            for event in self.select(gui, series[record_index - 1]):
                device.execute(event)
                _, result = device.execute(series[record_index].event)
                if result:
                    return [event], series[record_index].event
            # TODO whether to search?
            device.stop_and_restart(series.get_before_record_series(record_index))
            for event in self.construct_event_series(device, record_series):
                device.execute(event)
            return list(self.construct_event_series(device, record_series))


if __name__ == '__main__':
    l = [1, 2, 3, 4, 5]
    map()
