import xml.etree.ElementTree as et
import uiautomator2 as u2
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
        if apk_.get_package() not in get_all_installed_package(self.u):
            install_grant_runtime_permissions(self.u, apk_path)
        self.package = apk_.get_package()

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
            elif type(event) == list:
                for e in event:
                    event_action_lambda_map[e.action](self, event)
            return True
        except RuntimeError:
            return False

    def select_widget(self, selector):
        pass


if __name__ == '__main__':
    d = Device(apk_path='../../benchmark/simpleCalendarPro/simpleCalendarPro6.16.1.apk')
    # app_node = d.get_ui_info_by_package()
