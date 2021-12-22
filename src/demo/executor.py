from demo.device import Device
from demo.analyst import Analyst
from demo.series import Series
from demo.repair import Repair
import logging

executor_log = logging.getLogger('executor')
executor_log.setLevel(logging.DEBUG)
executor_log_ch = logging.StreamHandler()
executor_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
executor_log_ch.setFormatter(formatter)
executor_log.addHandler(executor_log_ch)


class Executor:
    def __init__(self, device: Device, analysis: Analyst, series: Series, repair: Repair, verbose):
        self.device = device
        self.analysis = analysis
        self.series = series
        self.repair = repair
        self.repaired_events = []
        self.verbose = verbose
        if self.verbose:
            executor_log_ch.setLevel(logging.DEBUG)
        else:
            executor_log_ch.setLevel(logging.INFO)
        pass

    def execute(self):
        for i in range(len(self.series)):
            record = self.series[i]
            executor_log.info('now execute record ' + str(i))
            executor_log.debug(record.__str__())
            _, result = self.device.execute(record.event)
            executor_log.info('result: {}'.format(result))
            if result:
                self.repaired_events.append(record.event)
                continue
            else:
                gui = self.device.get_ui_info()
                events = self.repair.select(gui, record)
                is_successful = False
                executor_log.info('try to repair this event')
                for event in events:
                    executor_log.info('try event')
                    executor_log.debug(event.__str__())
                    gui, execute_result = self.device.execute(event)
                    result = self.analysis.is_right_repair(execute_result, record.xml)
                    if result:
                        is_successful = True
                        break
                    self.device.stop_and_restart(self.series[:i])
                if is_successful:
                    continue
                repair_events, now_event = self.repair.recovery(self.series, self.device, i)
                for i in range(len(repair_events)):
                    self.repaired_events.pop()
                for event in repair_events:
                    self.repaired_events.append(event)
                self.repaired_events.append(now_event)

    def insert_new_event(self):
        pass
