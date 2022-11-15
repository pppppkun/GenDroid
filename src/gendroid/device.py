import os
import time
import traceback
import uiautomator2 as u2
from uiautomator2.exceptions import BaseError
from gendroid.event import Event, send_event_to_device, build_event
from androguard.core.bytecodes.apk import APK
from gendroid.FSM import FSM
import logging
import copy

device_log = logging.getLogger('device')
device_log.setLevel(logging.DEBUG)
device_log_ch = logging.StreamHandler()
device_log_ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
device_log_ch.setFormatter(formatter)
device_log.addHandler(device_log_ch)


class Device:
    def __init__(self, apk_path, graph: FSM, have_install=False, device='emulator-5554'):
        self.u = u2.connect(device)
        apk_ = APK(apk_path)
        self.apk_path = apk_path
        self.graph = graph
        self.package = apk_.get_package()
        self.keep_app = have_install
        if have_install:
            pass
        else:
            if apk_.get_package() in self.get_all_installed_package():
                self.u.app_uninstall(self.package)
            self.install_grant_runtime_permissions(apk_path)
        self.u.app_stop(self.package)
        self.start_app()
        self.u.sleep(2)
        self.history = []

    def gui(self):
        return self.u.dump_hierarchy()

    def info(self):
        info = self.u.info
        return info

    # TODO add_edge and add_node need to be add here to prevent scattered and difficult management
    def execute(self, event, is_add_edge=True):
        try:
            if type(event) == Event:
                event = [event]
            for e in event:
                pre_info = self.app_current_with_gui()
                send_event_to_device[e.action](self, e)
                self.history.append(e)
                self.interval()
                post_info = self.app_current_with_gui()
                if is_add_edge:
                    self.graph.add_edge(
                        pre_info,
                        post_info,
                        e
                    )
                    continue
                    # 1. try back
                    # 2. try to re-execute last event
                    # 3. if no error, add back edge to post_info -> back_info
                    if not self.graph.have_path_between_device_info(post_info, pre_info) and e.action == 'click':
                        # try back
                        device_log.info('try to add back-edge')
                        back_event = build_event(action='back', selector=None, data=None)
                        send_event_to_device[back_event.action](self, back_event)
                        self.interval()
                        # try to re-execute last event
                        back_info = self.app_current_with_gui()
                        try:
                            send_event_to_device[e.action](self, e)
                        except BaseError as be:
                            device_log.error(f'failed to re-execute {e.__str__()} when try to add back edge')
                            device_log.error(be)
                            # recovery
                            device_log.info('try to recovery to last event')
                            self.reset(len(self.history))
                        else:
                            # no error, add back edge from post_info -> back_info
                            self.interval()
                            self.graph.add_edge(
                                post_info,
                                back_info,
                                back_event
                            )

            if self.u.info['currentPackageName'] != self.package:
                return self.gui(), False
            return self.gui(), True
        except BaseError:
            device_log.error('can not execute event')
            traceback.print_exc()
            return self.gui(), False

    def try_execute(self, e):
        pre_info = self.app_current_with_gui()
        pre_state = self.graph.get_temp_state_id(pre_info)
        send_event_to_device[e.action](self, e)
        self.interval()
        post_info = self.app_current_with_gui()
        post_state = self.graph.get_temp_state_id(post_info)
        if pre_state != post_state:
            # self.reset(len(self.history))
            self.history.append(e)
            self.graph.add_edge(
                pre_info,
                post_info,
                e
            )
            return True
        return False

    def select_widget(self, selector):
        translate = {
            'text': 'text',
            'content-desc': 'descriptionContains',
            'index': 'index',
            'resource-id': 'resourceId',
            'class': 'className'
        }
        new_selector = {}
        for x in translate:
            if x in selector and selector[x]:
                new_selector[translate[x]] = selector[x]
        # temp = dict(map(lambda x: (translate[x], selector[x]), selector))
        w = self.u(**new_selector)
        if w.exists():
            return w
        if 'className' in new_selector and 'EditText' in new_selector['className']:
            if 'text' in new_selector:
                new_selector.pop('text')
        if 'descriptionContains' in new_selector and 'Show Navigation Drawer' == new_selector['descriptionContains']:
            new_selector['descriptionContains'] = 'Navigate up'
        return self.u(**new_selector)

    def select_widget_wrapper(self, selector):
        widget = self.select_widget(selector).info
        n_w = dict()
        n_w['class'] = widget['className']
        n_w['content-desc'] = widget['contentDescription']
        n_w['package'] = widget['packageName']
        n_w['resource-id'] = widget['resourceName']
        n_w['text'] = "" if widget['text'] is None else widget['text']
        n_w['activity'] = self.activity()
        n_w['bounds'] = widget['bounds']
        return n_w

    def exists_widget(self, selector: dict):
        widget = self.select_widget(selector)
        if widget.exists():
            return True
        # up or lower of text
        else:
            if 'text' in selector and selector['text']:
                if 'class' in selector and 'EditText' in selector['class']:
                    new_selector = copy.deepcopy(selector)
                    new_selector.pop('text')
                    widget = self.select_widget(new_selector)
                    return widget.exists()
                else:
                    new_selector = copy.deepcopy(selector)
                    new_selector['text'] = new_selector['text'].upper()
                    widget = self.select_widget(new_selector)
                    return widget.exists()

    def close_keyboard(self):
        if 'com.google.android.inputmethod.latin:id/key_pos' in self.gui():
            self.u.press(key='back')
        self.u.sleep(2)

    def screenshot(self):
        file_name = str(int(time.time())) + '.png'
        self.u.screenshot(os.path.join('screenshots', file_name))
        return file_name

    def widget_screenshot(self, widget):
        if self.exists_widget(widget):
            return self.select_widget(widget).screenshot()
        else:
            return None

    def interval(self):
        self.u.sleep(4)
        self.close_keyboard()

    def app_current(self):
        return self.u.app_current()

    def app_current_with_gui(self):
        app_current = self.app_current()
        app_current['gui'] = self.gui()
        return app_current

    def activity(self):
        return self.u.app_current()['activity']

    # need a more efficiency way.
    def stop_and_restart(self, events=None):
        self.u.app_stop(self.package)
        if not self.keep_app:
            self.u.app_uninstall(self.package)
            self.install_grant_runtime_permissions(self.apk_path)
        # self.u.app_start(self.package)
        self.start_app()
        if events:
            for event in events:
                send_event_to_device[event.action](self, event)
                self.u.sleep(5)
                self.close_keyboard()

    def install_grant_runtime_permissions(self, data):
        target = "/data/local/tmp/_tmp.apk"
        self.u.app_install(data)
        self.u.push(data, target, show_progress=True)
        ret = self.u.shell(['pm', 'install', "-r", "-t", "-g", target], timeout=300)
        if ret.exit_code != 0:
            raise RuntimeError(ret.output, ret.exit_code)

    def get_all_installed_package(self):
        ret = self.u.shell("pm list packages -f")
        if ret.exit_code == 0:
            return ret.output

    def reset(self, checkpoint):
        self.u.sleep(2)
        self.history = self.history[:checkpoint]
        self.stop_and_restart(events=self.history)

    def set_checkpoint(self):
        return len(self.history)

    def start_app(self):
        if 'chrome' in self.package:
            ret = self.u.shell('am start -n com.android.chrome/com.google.android.apps.chrome.Main', timeout=300)
            self.u.sleep(2)
            if ret.exit_code == 1:
                exit(1)
            return
        if 'googlequick' in self.package:
            self.u.app_start('com.google.android.googlequicksearchbox',
                             activity='com.google.android.apps.gsa.searchnow.SearchNowActivity', use_monkey=True)
            return
        self.u.app_start(package_name=self.package, wait=True, use_monkey=True)
        self.u.sleep(4)


if __name__ == '__main__':
    # d = Device(apk_path='../../benchmark/simpleCalendarPro/simpleCalendarPro.apk')
    # app_node = d.get_ui_info_by_package()
    d = u2.connect()
    var = d(resourceId='org.secuso.privacyfriendlytodolist:id/fab_new_task').info
    print(var)
