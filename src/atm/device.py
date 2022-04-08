import xml.etree.ElementTree as et
import uiautomator2 as u2
from uiautomator2.exceptions import BaseError
from atm.event import Event, send_event_to_device
from androguard.core.bytecodes.apk import APK


class Device:
    def __init__(self, apk_path, graph, serial=None):
        if serial:
            self.u = u2.connect(serial)
        else:
            self.u = u2.connect()
        apk_ = APK(apk_path)
        self.apk_path = apk_path
        self.graph = graph
        self.package = apk_.get_package()
        if apk_.get_package() in self.get_all_installed_package():
            self.u.app_uninstall(self.package)
        self.install_grant_runtime_permissions(apk_path)
        self.u.app_start(package_name=self.package, wait=True)
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
                self.u.sleep(2)
                self.close_keyboard()
                post_info = self.app_current_with_gui()
                if is_add_edge:
                    self.graph.add_edge(
                        pre_info,
                        post_info,
                        e
                    )
            if self.u.info['currentPackageName'] != self.package:
                return self.gui(), False
            return self.gui(), True
        except BaseError:
            return self.gui(), False

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
        return n_w

    def exists_widget(self, selector: dict):
        widget = self.select_widget(selector)
        if widget.exists():
            return True
        # up or lower of text
        else:
            if 'text' in selector:
                selector['text'] = selector['text'].upper()
            widget = self.select_widget(selector)
            if widget.exists():
                return True
            if 'text' in selector:
                selector.pop('text')
            widget = self.select_widget(selector)
            if widget.exists():
                return True
            return False

    def close_keyboard(self):
        if 'com.google.android.inputmethod.latin' in self.gui():
            self.u.press(key='back')
        self.u.sleep(2)

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
        self.u.app_uninstall(self.package)
        self.install_grant_runtime_permissions(self.apk_path)
        self.u.app_start(self.package)
        if events:
            for event in events:
                send_event_to_device[event.action](self, event)
                self.u.sleep(2)
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
