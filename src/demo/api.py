import os

from demo.event import event_factory, VirtualEvent, EventData
from demo.record import record_events
from scripts.convert import gui_xml2json
from demo.construct import Constructor
from demo.device import Device
from demo.executor import Executor
import time


def get_info_and_screenshot(device):
    import os
    return device.u.app_current(), device.u.screenshot(
        os.path.join('img', str(int(time.time())) + '.jpg')), device.u.dump_hierarchy()


def build_event(selector, action, data=None):
    # e_data = {'selector': selector, 'action': action}
    # if action_data:
    #     e_data['action_data'] = action_data
    e_data = EventData(action=action, selector=selector, data=data)
    return event_factory[e_data.action](e_data)


def execute_and_record(description_, events, device, executor):
    pre_info, pre_screenshot, pre_xml = get_info_and_screenshot(device)
    widgets = []
    events_ = []
    for event in events:
        widgets.append(device.select_widget(event.selector).info)
        events_.append(event.to_dict())
        executor.direct_execute(event)
    device.u.sleep(3)
    post_info, post_screenshot, post_xml = get_info_and_screenshot(device)
    record_events(
        description=description_,
        event_series=events_,
        widgets=widgets,
        pre_screenshot=pre_screenshot,
        pre_device_info=pre_info,
        post_screenshot=post_screenshot,
        post_device_info=post_info,
        pre_xml=gui_xml2json(pre_xml, activity_name=get_s2v_activity_name(pre_info)),
        post_xml=gui_xml2json(post_xml, activity_name=get_s2v_activity_name(post_info))
    )


def get_s2v_activity_name(info):
    return info['package'] + '/' + info['package'] + info['activity']


def build_virtual_event(description_, data=None):
    return VirtualEvent(description_, data)


def set_app(apk_folder, app_name):
    """
    1. apktool d {apk} -f -o apk_folder/{decompile}
    2. mkdir apk_folder/out
    :param apk_folder:
    :param app_name:
    :return:
    """
    td_path = '/Users/pkun/PycharmProjects/ui_api_automated_test/TrimDroid.jar'
    apk = os.path.join(apk_folder, app_name + ".apk")
    decompile = os.path.join(apk_folder, 'decompile')
    out = os.path.join(apk_folder, 'out')
    os.system(f'mkdir {decompile}')
    os.system(f'mkdir {out}')
    os.system(f'apktool d {apk} -f -o {decompile}')
    os.system(f'java -jar {td_path} {apk_folder} {app_name} {out}')
    pass


class Tester:
    def __init__(self, apk_path):
        self.device = Device(apk_path)
        self.constructor = Constructor(analyst=None)
        self.executor = Executor(device=self.device, series=None, constructor=self.constructor, verbose='debug')
        self.virtual_event = []
        self.device.u.sleep(5)

    def add_description(self, description, data=None):
        self.virtual_event.append(build_virtual_event(description, data))
        return self

    def construct(self):
        for ve in self.virtual_event:
            self.executor.construct_new_event(ve)
        self.executor.to_scripts()

    def print_script(self):
        self.executor.to_scripts()


if __name__ == '__main__':
    set_app('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/AcDisplay', 'AcDisplay')
