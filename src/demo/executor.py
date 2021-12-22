from demo.device import Device
from demo.analyst import Analyst
from demo.series import Series
from demo.repair import Repair
import logging

log = logging.getLogger('executor')
log.setLevel(logging.DEBUG)


class Executor:
    def __init__(self, device: Device, analysis: Analyst, series: Series, repair: Repair):
        self.device = device
        self.analysis = analysis
        self.series = series
        self.repair = repair
        self.repaired_events = []
        pass

    def execute(self):
        for i in range(len(self.series)):
            record = self.series[i]
            log.debug(str(i) + ' ' + record.__str__())
            _, result = self.device.execute(record.event)
            log.debug('result ', result)
            if result:
                self.repaired_events.append(record.event)
                continue
            else:
                gui = self.device.get_ui_info()
                events = self.repair.select(gui, record)
                is_successful = False
                log.debug('try to repair this event')
                for event in events:
                    log.debug('try event:' + event)
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
