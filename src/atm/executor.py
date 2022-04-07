from atm.analyst import Analyst
from atm.construct import Constructor
from atm.device import Device
import logging

executor_log = logging.getLogger('executor')
executor_log.setLevel(logging.DEBUG)
executor_log_ch = logging.StreamHandler()
executor_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
executor_log_ch.setFormatter(formatter)
executor_log.addHandler(executor_log_ch)


class Executor:
    def __init__(self, analyst: Analyst, constructor: Constructor, device: Device):
        self.analyst = analyst
        self.constructor = constructor
        self.device = device
        pass

    # 1. get widget dynamic and static.
    # 2. calculate similarity between source and d and get widget w1
    # 3. calculate similarity between destination and s and get widget w2
    # 4. calculate paths from activity[after execute w1] to activity[which has w2]
    # widgets = get_all_widgets()
    # calculated similarity between <widgets source>, <widgets destination>
    def execute(self, ves):
        for i in range(len(ves) - 1):
            src_des = ves[i].description
            tgt_des = ves[i + 1].description
            executor_log.info(f'generating event for "{src_des}"')
            src_widget = self.analyst.dynamic_match_widget(src_des)
            executor_log.info(f'match widget f{src_widget.__str__()}')
            src_event = self.constructor.generate_events_from_widget(widget=src_widget, action=None, data=ves[i].data)
            self.device.execute(src_event)
            tgt_widgets = self.analyst.static_match_activity(tgt_des)
            for tgt_widget in tgt_widgets:
                path = self.analyst.calculate_path_between_activity(src_des, tgt_widget)
                if path is not None:
                    executor_log.info(f'execute path')
                    events = path[0]
                    self.device.execute(events, is_add_edge=False)
                    # events = self.constructor.generate_events_from_widget(path)
                    # self.device.execute(events)
                    break
            # no path have found
            ns, ss = self.analyst.event_expansion(tgt_des)
            es = list(
                map(lambda x: self.constructor.generate_event_from_node(x, action='set_text',
                                                                        data={'text': 'hello'}),
                    ns
                    ),
            )
            self.device.execute(es)

        src_des = ves[len(ves) - 1].description
        executor_log.info(f'generating event for "{src_des}"')
        src_widget = self.analyst.dynamic_match_widget(src_des)
        executor_log.info(f'match widget f{src_widget.__str__()}')
        src_event = self.constructor.generate_events_from_widget(src_widget, None, ves[len(ves) - 1].data)
        self.device.execute(src_event)

    def record(self, events):
        for event in events:
            self.device.execute(event)

    def to_scripts(self):
        scripts = \
            """
import uiautomator2 as u2
d = u2.connect()
d.app_stop('{}')
d.app_start('{}')
            """.format(self.device.package, self.device.package)
        for event in self.device.history:
            scripts += event.to_uiautomator2_format() + \
                       """
d.sleep(3)
if 'com.google.android.inputmethod.latin' in d.dump_hierarchy():
   d.press(key='back')
"""
        f = open('test_script.py', 'w')
        f.write(scripts)
