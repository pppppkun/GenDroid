from demo.device import Device
from demo.analyst import Analyst
from demo.series import Series
from demo.construct import Constructor
import logging

executor_log = logging.getLogger('executor')
executor_log.setLevel(logging.DEBUG)
executor_log_ch = logging.StreamHandler()
executor_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
executor_log_ch.setFormatter(formatter)
executor_log.addHandler(executor_log_ch)


class Executor:
    def __init__(self, device: Device, analysis: Analyst, series: Series, constructor: Constructor, verbose):
        self.device = device
        self.analysis = analysis
        self.series = series
        self.constructor = constructor
        self.verbose = verbose
        self.record_point = 0
        self.event_stack = []
        if self.verbose:
            executor_log_ch.setLevel(logging.DEBUG)
        else:
            executor_log_ch.setLevel(logging.INFO)
        pass

    def execute(self):
        while self.record_point < len(self.series):
            record = self.series[self.record_point]
            executor_log.info('now construct record ' + str(self.record_point))
            if record.event:
                self.direct_execute(record)
            else:
                self.construct_new_event(record)

    def construct_new_event(self, record):
        # executor_log.info('now construct record ' + str(record_index))
        executor_log.debug(record.__str__())
        events = self.constructor.construct(self.device.get_ui_info_by_package(), record)
        while len(events) != 0:
            event = events.popleft()
            executor_log.debug('try event ' + event.__str__())
            gui, executor_result = self.device.execute(event)
            if executor_result:
                self.record_point += 1
                self.event_stack.append([events, event])
                break

    def direct_execute(self, record):
        executor_log.debug(record.__str__())
        gui, execute_result = self.device.execute(record.event)
        executor_log.info('execute_result: {}'.format(execute_result))
        if execute_result:
            self.record_point += 1
            self.event_stack.append(record)
        else:
            self.back_tracking()

    def back_tracking(self):
        events = map(lambda x: x[1] if type(x) is list else x, self.event_stack)
        self.device.stop_and_restart(events)
