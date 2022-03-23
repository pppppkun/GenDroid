import os
from demo.record import record_events
import time


def get_info_and_screenshot(device):
    import os
    return device.u.app_current(), device.u.screenshot(
        os.path.join('img', str(int(time.time())) + '.jpg')), device.u.dump_hierarchy()


def build_event(selector, action, data=None):
    pass


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
        pre_xml=pre_xml,
        post_xml=post_xml
    )


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
        pass

    def add_description(self, description, data=None):
        pass

    def construct(self):
        pass

    def print_script(self):
        pass
