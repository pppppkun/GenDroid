import xml.etree.ElementTree as et
import uiautomator2 as u2
from uiautomator2.exceptions import BaseError
from demo.adb import install_grant_runtime_permissions, get_all_installed_package
from androguard.core.bytecodes.apk import APK
from demo.event import send_event_to_device, Event


class EventError(RuntimeError):
    def __init__(self, t, obj):
        super.__init__(t, obj)


class Device:
    def __init__(self, apk_path, serial=None):
        if serial:
            self.u = u2.connect(serial)
        else:
            self.u = u2.connect()
        apk_ = APK(apk_path)
        self.apk_path = apk_path
        self.package = apk_.get_package()
        if apk_.get_package() in get_all_installed_package(self.u):
            self.u.app_uninstall(self.package)
        install_grant_runtime_permissions(self.u, apk_path)
        self.u.app_start(package_name=self.package, wait=True)

    def ui_info_by_package(self):
        ui_info = self.u.dump_hierarchy()
        root = et.fromstring(ui_info)
        try:
            package_node = et.tostring(root.find(".*[@package='" + self.package + "']")).decode('utf-8')
        except:
            package_node = ui_info
        return package_node

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

    # need a more efficiency way.
    # TODO
    def stop_and_restart(self, events=None):
        self.u.app_stop(self.package)
        self.u.app_uninstall(self.package)
        install_grant_runtime_permissions(self.u, self.apk_path)
        self.u.app_start(self.package)
        if events:
            for event in events:
                send_event_to_device[event.action](self, event)
                self.u.sleep(2)


if __name__ == '__main__':
    # d = Device(apk_path='../../benchmark/simpleCalendarPro/simpleCalendarPro6.16.1.apk')
    # app_node = d.get_ui_info_by_package()
    d = u2.connect()
    # d.info
