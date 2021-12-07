import xml.etree.ElementTree as et
from demo.adb import *
from androguard.core.bytecodes.apk import APK


class EventDoError(RuntimeError):
    def __init__(self, t, obj):
        super.__init__(t, obj)


class Device:
    def __init__(self, apk_path=None, serial=None):
        if serial:
            self.u = u2.connect(serial)
        else:
            self.u = u2.connect()
        if apk_path:
            apk_ = APK(apk_path)
            if apk_.get_package() not in get_all_installed_package(self.u):
                install_grant_runtime_permissions(self.u, apk_path)

    def get_ui_info_by_package(self, selector):
        ui_info = self.u.dump_hierarchy()
        root = et.fromstring(ui_info)
        result = []
        for child in root.iter():
            if 'package' in child.attrib and child.attrib['package'] == selector:
                result.append(child)
        return result

    def get_ui_info(self):
        return self.u.dump_hierarchy()

    def do_event(self, event):
        if event:
            pass
        else:
            raise EventDoError(event) from RuntimeError


if __name__ == '__main__':
    d = Device(apk_path='../../benchmark/simpleCalendarPro/simpleCalendarPro6.16.1.apk')
    # app_node = d.get_ui_info_by_package()
