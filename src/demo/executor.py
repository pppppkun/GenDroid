from demo.device import Device
from demo.analyst import Analyst
from demo.series import Series, EventSeries
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
    def __init__(self, device: Device, analysis: Analyst, series, constructor: Constructor, verbose):
        self.device = device
        self.analysis = analysis
        self.series = series
        self.constructor = constructor
        self.verbose = verbose
        self.record_point = 0
        self.event_stack = EventSeries()
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
        events = self.constructor.construct(self.device.ui_info(), record)
        while len(events) != 0:
            event = events.popleft()
            executor_log.debug('try event ' + event.__str__())
            gui, executor_result = self.device.execute(event)
            if executor_result:
                self.record_point += 1
                self.event_stack.append([events, event])
                break
            else:
                if len(events) == 0:
                    # need to back_tracking
                    if self.event_stack.last_item_type() is list:
                        # back_tracking
                        self.back_tracking()
                    else:
                        # can't construct
                        executor_log.error("last execute event is implemented.")
                        exit(-1)
                else:
                    expect_last_events = self.event_stack.get_events()
                    self.device.stop_and_restart(expect_last_events)

    def direct_execute(self, record):
        executor_log.debug(record.__str__())
        gui, execute_result = self.device.execute(record.event)
        executor_log.info('execute_result: {}'.format(execute_result))
        if execute_result:
            self.record_point += 1
            self.event_stack.append(record)
        else:
            if type(self.event_stack[-1]) is list:
                self.back_tracking()
            else:
                executor_log.error("continuity implemented event can only execute the last one")
                exit(-1)

    # TODO
    # 1. the last event device successfully executed is implemented, never need to back_tracking.
    # 2. if come from direct execute, the last event device executed must be construct event.
    # 3. if come from construct execute
    #   3.1 if the last execute event is implemented, -> can't construct
    #   3.2 if the last execute event is non-implemented, -> back to it and iterator.
    def back_tracking(self):
        self.record_point -= 1
        expect_last_events = self.event_stack.get_events_expect_last()
        last_event = self.event_stack[-1]
        self.device.stop_and_restart(expect_last_events)
        construct_events = last_event[0]
        new_event = construct_events.popleft()
        self.event_stack[-1] = [construct_events, new_event]
        self.device.execute(new_event)
