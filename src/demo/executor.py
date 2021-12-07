from demo.device import Device, EventDoError
from demo.analyst import Analyst
from demo.series import Series


class Executor:
    def __init__(self, device: Device, analysis: Analyst, series: Series):
        self.device = device
        self.analysis = analysis
        self.series = series
        pass

    def execute(self):
        for event, result in self.series.iter():
            events = self.analysis.confidence(event)
            events.append(0, event)
            flag = 0
            for event_ in events:
                result_ = self.device.do_event(event_)
                compare = self.analysis.analysis_result(result, result_)
                if compare == 'SUCCESS':
                    flag = 1
                    break
            if flag == 0:
                self.series.error_recover()
                
