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
        self.repaired_events = []
        self.verbose = verbose
        self.gui_stack = []
        self.select_events_stack = []
        if self.verbose:
            executor_log_ch.setLevel(logging.DEBUG)
        else:
            executor_log_ch.setLevel(logging.INFO)
        pass

    def execute(self):
        for i in range(len(self.series)):
            record = self.series[i]
            if record.action:
                self.direct_execute(record_index=i)
            else:
                self.construct_new_event(record_index=i)

    def construct_new_event(self, record_index):
        record = self.series[record_index]
        executor_log.info('now construct record ' + str(record_index))
        executor_log.debug(record.__str__())
        events = self.constructor.construct(self.device.get_ui_info_by_package(), record)
        for event in events:
            executor_log.debug(event.__str__())
            gui, execute_result = self.device.execute(event)
            if execute_result:
                record.event = event
                self.repaired_events.append(event)
                break

    def direct_execute(self, record_index):
        record = self.series[record_index]
        executor_log.info('now execute record ' + str(record_index))
        executor_log.debug(record.__str__())
        gui, execute_result = self.device.execute(record.event)
        executor_log.info('execute_result: {}'.format(execute_result))
        if execute_result:
            self.repaired_events.append(record.event)
            self.gui_stack.append(gui)
        else:
            events = self.constructor.select(gui, record)
            is_successful = False
            executor_log.info('try to repair this event ' + record.event.__str__())
            for event in events:
                executor_log.debug(event.__str__())
                gui, execute_result = self.device.execute(event)
                executor_log.info('execute_result: {}'.format(execute_result))
                if execute_result:
                    result = self.analysis.is_same_gui(gui, record.xml)
                    if result:
                        is_successful = True
                        self.repaired_events.append(events)
                        self.gui_stack.append(gui)
                        break
                self.device.stop_and_restart(self.series[:record_index])
            if is_successful:
                return
