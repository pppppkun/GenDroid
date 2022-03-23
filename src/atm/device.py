import xml.etree.ElementTree as et
import uiautomator2 as u2
from uiautomator2.exceptions import BaseError
from atm.event import Event, send_event_to_device
from androguard.core.bytecodes.apk import APK


class Device:
    def __init__(self, apk_path, serial=None):
        if serial:
            self.u = u2.connect(serial)
        else:
            self.u = u2.connect()
        apk_ = APK(apk_path)
        self.apk_path = apk_path
        self.package = apk_.get_package()
        if apk_.get_package() in self.get_all_installed_package():
            self.u.app_uninstall(self.package)
        self.install_grant_runtime_permissions(apk_path)
        self.u.app_start(package_name=self.package, wait=True)
        self.history = []

    def get_gui(self):
        return self.u.dump_hierarchy()

    def info(self):
        return self.u.info

    def execute(self, event):
        try:
            if type(event) == Event:
                send_event_to_device[event.action](self, event)
                self.u.sleep(2)
            elif type(event) == list:
                for e in event:
                    send_event_to_device[e.action](self, event)
                    self.u.sleep(2)
            if self.u.info['currentPackageName'] != self.package:
                return self.get_gui(), False
            self.close_keyboard()
            return self.get_gui(), True
        except BaseError:
            return self.get_gui(), False

    def select_widget(self, selector):
        translate = {
            'text': 'text',
            'content-desc': 'descriptionContains',
            'index': 'index',
            'resource-id': 'resourceId',
            'class': 'className'
        }
        temp = dict(map(lambda x: (translate[x], selector[x]), selector))
        return self.u(**temp)

    def select_widget_wrapper(self, selector):
        widget = self.select_widget(selector).info
        n_w = dict()
        n_w['class'] = widget['className']
        n_w['content-desc'] = widget['contentDescription']
        n_w['package'] = widget['packageName']
        n_w['resource-id'] = widget['resourceName']
        n_w['text'] = "" if widget['text'] is None else widget['text']
        n_w['activity'] = self.ac

    def exists_widget(self, selector):
        widget = self.select_widget(selector)
        return widget.exists

    def close_keyboard(self):
        if 'main_keyboard_frame' in self.get_gui():
            self.u.press(key='back')

    def app_current(self):
        return self.u.app_current

    def activity(self):
        return self.u.app_current['activity']

    # need a more efficiency way.
    def stop_and_restart(self, events=None):
        self.u.app_stop(self.package)
        self.u.app_uninstall(self.package)
        self.install_grant_runtime_permissions(self.apk_path)
        self.u.app_start(self.package)
        if events:
            for event in events:
                send_event_to_device[event.action](self, event)
                self.u.sleep(2)

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
        self.history = self.history[:checkpoint]
        self.stop_and_restart(events=self.history)

    def set_checkpoint(self):
        return len(self.history)


if __name__ == '__main__':
    # d = Device(apk_path='../../benchmark/simpleCalendarPro/simpleCalendarPro6.16.1.apk')
    # app_node = d.get_ui_info_by_package()
    d = u2.connect()
    var = d(resourceId='org.secuso.privacyfriendlytodolist:id/fab_new_task').info
    print(var)
