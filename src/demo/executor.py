from demo.device import Device, EventError
from demo.analyst import Analyst
from demo.series import Series
from demo.repair import Repair


class Executor:
    def __init__(self, device: Device, analysis: Analyst, series: Series, repair: Repair):
        self.device = device
        self.analysis = analysis
        self.series = series
        self.repair = repair
        self.repaired_event = []
        pass

    def execute(self):
        for i in range(len(self.series)):
            record = self.series[i]
            result = self.device.execute(record.event)
            if result:
                continue
            else:
                gui = self.device.get_ui_info()
                events = self.repair.select(gui, record)
                is_successful = False
                for j in range(len(events)):
                    new_event = events[j]
                    actual_result = self.device.execute(new_event)
                    result = self.analysis.is_right_repair(actual_result, record.xml)
                    if result:
                        is_successful = True
                        break
                if is_successful:
                    continue
                result = self.repair.recovery(self.series[i+1], self.device)
