import xml.etree.ElementTree as et
import uiautomator2 as u2
from uiautomator2.exceptions import BaseError
from demo.adb import install_grant_runtime_permissions, get_all_installed_package
from androguard.core.bytecodes.apk import APK
from demo.event import event_action_lambda_map, Event


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

    def get_ui_info_by_package(self):
        ui_info = self.u.dump_hierarchy()
        root = et.fromstring(ui_info)
        package_node = root.find(".*[@package='" + self.package + "']")
        return package_node

    def get_ui_info(self):
        return self.u.dump_hierarchy()

    def execute(self, event):
        try:
            if type(event) == Event:
                event_action_lambda_map[event.action](self, event)
                self.u.sleep(1)
            elif type(event) == list:
                for e in event:
                    event_action_lambda_map[e.action](self, event)
                    self.u.sleep(1)
            return self.u.dump_hierarchy(), True
        # maybe too much
        except BaseError:
            return None, False

    def select_widget(self, selector):
        temp = dict()
        translate = {
            'text': 'text',
            'content-desc': 'descriptionContains',
            'index': 'index',
            'resource-id': 'resourceId',
            'class': 'className'
        }
        for i in selector:
            temp[translate[i]] = selector[i]
        return self.u(**temp)

    # need a more efficiency way.
    # TODO
    def stop_and_restart(self, events):
        self.u.app_stop(self.package)
        self.u.app_uninstall(self.package)
        install_grant_runtime_permissions(self.u, self.apk_path)
        self.u.app_start(self.package)
        for event in events:
            event_action_lambda_map[event.action](self, event)


if __name__ == '__main__':
    d = Device(apk_path='../../benchmark/simpleCalendarPro/simpleCalendarPro7.apk')
    # app_node = d.get_ui_info_by_package()
