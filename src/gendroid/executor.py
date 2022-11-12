from gendroid.analyst import Analyst
from gendroid.construct import Constructor
from gendroid.device import Device
from enum import Enum
import logging

executor_log = logging.getLogger('executor')
executor_log.setLevel(logging.DEBUG)
executor_log_ch = logging.StreamHandler()
executor_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
executor_log_ch.setFormatter(formatter)
executor_log.addHandler(executor_log_ch)

PLACE_HOLDER = ''


class ExecutorMode(Enum):
    STATIC = 0
    DYNAMIC = 1
    HYBRID = 2


class Executor:
    def __init__(self, analyst: Analyst, constructor: Constructor, device: Device, mode=ExecutorMode.HYBRID):
        self.analyst = analyst
        self.constructor = constructor
        self.device = device
        self.descriptions = None
        self.mode = mode
        pass

    # 1. get widget dynamic and static.
    # 2. calculate similarity between source and d and get widget w1
    # 3. calculate similarity between destination and s and get widget w2
    # 4. calculate paths from activity[after execute w1] to activity[which has w2]
    # widgets = get_all_widgets()
    # calculated similarity between <widgets source>, <widgets destination>

    def dynamic_match(self, description, data):
        src_widgets = self.analyst.dynamic_match_widget(description)
        if len(src_widgets) != 1:
            for w in src_widgets:
                src_event = self.constructor.generate_events_from_widget(widget=w, action=None,
                                                                         data=data)
                r = self.device.try_execute(src_event)
                if r:
                    executor_log.info(f'match widget {w.__str__()}')
                    # self.device.execute(src_event)
                    break
        else:
            src_widget = src_widgets[0]
            src_event = self.constructor.generate_events_from_widget(widget=src_widget, action=None,
                                                                     data=data)
            executor_log.info(f'match widget {src_widget.__str__()}')
            self.device.execute(src_event)

    def execute(self, ves):
        self.descriptions = list(map(lambda x: x.description, ves))
        for i in range(len(ves) - 1):
            src_des = ves[i].description
            tgt_des = ves[i + 1].description
            if self.mode == ExecutorMode.HYBRID and i == 0:
                tgt_widgets = self.analyst.static_match_activity(src_des)
                tgt_widgets = list(tgt_widgets)
                if len(tgt_widgets) != 0:
                    tgt_widget = tgt_widgets[0]
                    # for tgt_widget in tgt_widgets:
                    path = self.analyst.calculate_path_between_activity(src_des, tgt_widget, resort_by_confidence=False)
                    if path is not None:
                        events = path[0]
                        executor_log.info('find path to first description')
                        self.device.execute(events, is_add_edge=False)

            executor_log.info(f'generating event for "{src_des}"')
            screenshot = self.device.screenshot()
            executor_log.info(f'screenshot is {screenshot}')
            self.dynamic_match(src_des, ves[i].data)
            if self.mode == ExecutorMode.DYNAMIC:
                continue
            tgt_widgets = self.analyst.static_match_activity(tgt_des)
            found_path = False
            i = 0
            for tgt_widget in tgt_widgets:
                i += 1
                if i == 5:
                    break
                path = self.analyst.calculate_path_between_activity(src_des, tgt_widget)
                if path is not None:
                    found_path = True
                    executor_log.info(f'find valid {len(path[0])} paths')
                    events = path[0]
                    executor_log.info(f'execute path with len {len(path[0])}')
                    self.device.execute(events, is_add_edge=False)
                    break
            if not found_path:
                # no path have found
                ns, ss = self.analyst.event_expansion(tgt_des)
                es = list(
                    map(lambda x: self.constructor.generate_event_from_node(x, action='set_text',
                                                                            data={'text': 'hello'}),
                        ns
                        ),
                )
                executor_log.info(f'cannot find any path and auto event expansion with len {len(es)}')
                self.device.execute(es)

        src_des = ves[-1].description
        executor_log.info(f'generating event for "{src_des}"')
        screenshot = self.device.screenshot()
        executor_log.info(f'screenshot is {screenshot}')
        self.dynamic_match(src_des, ves[-1].data)
        # src_widgets = self.analyst.dynamic_match_widget(src_des)
        # if len(src_widgets) != 1:
        #     for w in src_widgets:
        #         src_event = self.constructor.generate_events_from_widget(widget=w, action=None,
        #                                                                  data=ves[i].data)
        #         r = self.device.try_execute(src_event)
        #         if r:
        #             executor_log.info(f'match widget {w.__str__()}')
        #             self.device.execute(src_event)
        # else:
        #     src_widget = src_widgets[0]
        #     src_event = self.constructor.generate_events_from_widget(widget=src_widget, action=None,
        #                                                              data=ves[i].data)
        #     executor_log.info(f'match widget {src_widget.__str__()}')
        #     self.device.execute(src_event)

    def record(self, events):
        for event in events:
            self.device.execute(event)

    def to_scripts(self, file_name=None):
        scripts = \
            """
import uiautomator2 as u2
d = u2.connect()
d.app_stop('{}')
d.app_start('{}', use_monkey=True)
# {}
""".format(self.device.package, self.device.package, '.'.join(self.descriptions))
        for event in self.device.history:
            scripts += event.to_uiautomator2_format() + "\nd.sleep(3)\nif 'com.google.android.inputmethod.latin:id/key_pos' in d.dump_hierarchy():\n    d.press(key='back')\n"
        # from yapf.yapflib.yapf_api import FormatCode
        # scripts, _ = FormatCode(scripts)
        file_name = file_name if file_name is not None else 'test_script.py'
        f = open(file_name, 'w')
        f.write(scripts)
        f.close()


if __name__ == '__main__':
    # print(ExecutorMode['DYNAMIC'] == ExecutorMode.DYNAMIC)
    print(ExecutorMode(1))
