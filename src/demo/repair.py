"""
this class will give confidence between query and given node
"""
from demo.series import Series
from demo.device import Device
from demo.record import Record
from functools import reduce
from bert.api import predict_two_sentence
import xml.etree.ElementTree as et

# TODO fill the map
action_attrib_map = {
    'set_text': ['enabled', 'focusable'],
    'click': ['clickable'],
    'check': ['checkable'],
    'double_click': ['clickable'],
    'long_click': ['longClickable'],
    'swipe': [],
    'drag': [],
}

attributes = {
    'text',
    'content-desc',
    'resource-id'
}


def confidence(node: et.Element, description):
    result = (
        lambda x: [predict_two_sentence(description, attribute)[0] for attribute in get_node_attribute(x).values()])(
        node)
    result.sort(key=lambda x: -x)
    return result[0]


def get_node_attribute(node: et.Element):
    d = dict()
    for key in attributes:
        d[key] = node.get(key, None)
    return d


class FunctionWrap:
    def __init__(self, _data, f=None, _lambda=None):
        self.data = _data
        if f is None:
            self.f = None
        else:
            self.f = f(_lambda, _data)

    def append(self, f, _lambda):
        if self.f is None:
            self.f = f(_lambda, self.data)
        elif f is sorted:
            self.f = sorted(self.f, key=_lambda)
        else:
            self.f = f(_lambda, self.f)
        return self

    def iter(self):
        return self.f

    def do(self):
        if type(self.f) is not filter and type(self.f) is not map:
            return self.f
        else:
            return list(self.f)


class Repair:
    def __init__(self, strategy):
        self.strategy = strategy
        pass

    @staticmethod
    def select(gui, record):
        root = et.fromstringlist(gui)
        f = FunctionWrap((_node for _node in root.iter()))
        f.append(
            filter,
            lambda _node:
            FunctionWrap(
                f=reduce,
                _lambda=lambda x, y: x and y,
                _data=FunctionWrap(
                    f=map,
                    _lambda=lambda key: True if _node.get(key) == 'true' else False,
                    _data=action_attrib_map[record.action]
                ).iter()
            ).do()
        ).append(
            filter,
            lambda _node: True
        ).append(
            map,
            lambda x: (x, confidence(x, record.selector))
        ).append(
            sorted,
            lambda x: -x[1]
        )
        nodes_with_confidence = f.do()
        for node in nodes_with_confidence:
            yield node

    @staticmethod
    def construct_event_series(device: Device, record_series):
        yield 1
        pass

    def combine_select(self, es1, es2):
        pass

    # need a return format
    def recovery(self, series: Series, device: Device, record_index):
        if self.strategy == 'try_next':
            return series[record_index + 1]
        elif self.strategy == 'ERROR_RECOVERY':
            record_series = series.get_direct_record_series(record_index)
            relate_index = series.get_relate_index(record_index)
            device.stop_and_restart(series.get_before_record_series(record_index))
            # the line below is error, need to execute the all repair event in executor.
            _, _ = device.execute([record.event for record in record_index[: relate_index - 1]])
            # first: try to repair the last event
            # second: try to repair the whole event_series
            gui = device.get_ui_info()
            for event in self.select(gui, series[record_index - 1]):
                device.execute(event)
                _, result = device.execute(series[record_index].event)
                if result:
                    return [event], series[record_index].event
            # TODO whether to search?
            device.stop_and_restart(series.get_before_record_series(record_index))
            for event in self.construct_event_series(device, record_series):
                device.execute(event)
            return list(self.construct_event_series(device, record_series))

    def add_new_event(self, requirement):
        pass


if __name__ == '__main__':
    gui = '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\' ?>\r\n<hierarchy rotation="0">\r\n  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,63]">\r\n    <node index="1" text="" resource-id="com.android.systemui:id/status_bar_container" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,63]">\r\n      <node index="0" text="" resource-id="com.android.systemui:id/status_bar" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,63]">\r\n        <node index="0" text="" resource-id="com.android.systemui:id/status_bar_contents" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,63]">\r\n          <node index="0" text="" resource-id="com.android.systemui:id/notification_icon_area" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[16,0][804,63]">\r\n            <node index="0" text="" resource-id="com.android.systemui:id/notification_icon_area_inner" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[16,0][804,63]">\r\n              <node index="0" text="" resource-id="com.android.systemui:id/notificationIcons" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[16,0][804,63]">\r\n                <node index="0" text="" resource-id="" class="android.widget.ImageView" package="com.android.systemui" content-desc="Android System notification: Virtual SD card" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[142,0][205,63]" />\r\n                <node index="1" text="" resource-id="" class="android.widget.ImageView" package="com.android.systemui" content-desc="Gmail notification: 12 new messages" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[16,0][79,63]" />\r\n                <node index="2" text="" resource-id="" class="android.widget.ImageView" package="com.android.systemui" content-desc="Android System notification: USB debugging connected" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[205,0][268,63]" />\r\n                <node index="3" text="" resource-id="" class="android.widget.ImageView" package="com.android.systemui" content-desc="Android System notification: ATX is running in the background" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[79,0][142,63]" />\r\n              </node>\r\n            </node>\r\n          </node>\r\n          <node index="1" text="" resource-id="com.android.systemui:id/system_icon_area" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[804,0][1059,63]">\r\n            <node index="0" text="" resource-id="com.android.systemui:id/system_icons" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[804,0][947,63]">\r\n              <node index="1" text="" resource-id="com.android.systemui:id/signal_cluster" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[811,9][922,54]">\r\n                <node index="0" text="" resource-id="com.android.systemui:id/wifi_combo" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="Wifi signal full." checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[811,9][859,54]">\r\n                  <node index="2" text="" resource-id="com.android.systemui:id/wifi_signal" class="android.widget.ImageView" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[811,9][859,54]" />\r\n                </node>\r\n                <node index="2" text="" resource-id="com.android.systemui:id/mobile_signal_group" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[859,9][904,54]">\r\n                  <node index="0" text="" resource-id="com.android.systemui:id/mobile_combo" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="LTE Phone two bars." checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[859,9][904,54]">\r\n                    <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[859,9][904,54]">\r\n                      <node index="1" text="" resource-id="com.android.systemui:id/mobile_signal" class="android.widget.ImageView" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[859,9][904,54]" />\r\n                    </node>\r\n                  </node>\r\n                </node>\r\n              </node>\r\n              <node index="2" text="" resource-id="com.android.systemui:id/battery" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="Battery 100 percent." checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[922,0][947,63]">\r\n                <node index="0" text="" resource-id="" class="android.widget.ImageView" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[922,12][947,50]" />\r\n              </node>\r\n            </node>\r\n            <node index="1" text="11:18" resource-id="com.android.systemui:id/clock" class="android.widget.TextView" package="com.android.systemui" content-desc="11:18 PM" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[947,0][1059,63]" />\r\n          </node>\r\n        </node>\r\n      </node>\r\n    </node>\r\n    <node index="2" text="" resource-id="com.android.systemui:id/scrim_behind" class="android.view.View" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,63]" />\r\n    <node index="3" text="" resource-id="com.android.systemui:id/scrim_in_front" class="android.view.View" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,63]" />\r\n  </node>\r\n  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,1794]">\r\n    <node index="0" text="" resource-id="" class="android.widget.LinearLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,0][1080,1794]">\r\n      <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,63][1080,1794]">\r\n        <node index="0" text="" resource-id="com.simplemobiletools.calendar.pro:id/decor_content_parent" class="android.view.ViewGroup" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,63][1080,1794]">\r\n          <node index="0" text="" resource-id="com.simplemobiletools.calendar.pro:id/action_bar_container" class="android.widget.FrameLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,63][1080,210]">\r\n            <node index="0" text="" resource-id="com.simplemobiletools.calendar.pro:id/action_bar" class="android.view.ViewGroup" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,63][1080,210]">\r\n              <node index="0" text="" resource-id="" class="android.widget.ImageButton" package="com.simplemobiletools.calendar.pro" content-desc="Navigate up" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,63][147,210]" />\r\n              <node index="1" text="New Event" resource-id="" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[189,101][437,172]" />\r\n              <node index="2" text="" resource-id="" class="androidx.appcompat.widget.LinearLayoutCompat" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[953,63][1080,210]">\r\n                <node index="0" text="" resource-id="com.simplemobiletools.calendar.pro:id/save" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="Save" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[953,73][1080,199]" />\r\n              </node>\r\n            </node>\r\n          </node>\r\n          <node index="1" text="" resource-id="android:id/content" class="android.widget.FrameLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,210][1080,1794]">\r\n            <node index="0" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_scrollview" class="android.widget.ScrollView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="true" focused="false" scrollable="true" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,210][1080,1794]">\r\n              <node index="0" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_holder" class="android.widget.RelativeLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,210][1080,1794]">\r\n                <node index="0" text="Title" resource-id="com.simplemobiletools.calendar.pro:id/event_title" class="android.widget.EditText" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" visible-to-user="true" bounds="[42,252][1038,368]" />\r\n                <node index="1" text="nanjing" resource-id="com.simplemobiletools.calendar.pro:id/event_location" class="android.widget.EditText" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" visible-to-user="true" bounds="[42,410][912,526]" />\r\n                <node NAF="true" index="2" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_show_on_map" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[912,410][1038,526]" />\r\n                <node index="3" text="Description" resource-id="com.simplemobiletools.calendar.pro:id/event_description" class="android.widget.EditText" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="true" scrollable="false" long-clickable="true" password="false" selected="false" visible-to-user="true" bounds="[42,568][1038,684]" />\r\n                <node index="4" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_description_divider" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,726][1080,727]" />\r\n                <node index="5" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_time_image" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[32,759][137,907]" />\r\n                <node index="6" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_all_day_holder" class="android.widget.RelativeLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,759][1080,907]">\r\n                  <node index="0" text="All-day" resource-id="com.simplemobiletools.calendar.pro:id/event_all_day" class="android.widget.CheckBox" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="true" checked="true" clickable="false" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,791][1048,875]" />\r\n                </node>\r\n                <node index="7" text="December 10 (Fri)" resource-id="com.simplemobiletools.calendar.pro:id/event_start_date" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,907][548,1052]" />\r\n                <node index="8" text="December 10 (Fri)" resource-id="com.simplemobiletools.calendar.pro:id/event_end_date" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,1052][548,1197]" />\r\n                <node index="9" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_date_time_divider" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1218][1080,1219]" />\r\n                <node index="10" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_reminder_image" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[32,1240][137,1385]" />\r\n                <node index="11" text="10 minutes before" resource-id="com.simplemobiletools.calendar.pro:id/event_reminder_1" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,1240][1080,1385]" />\r\n                <node index="12" text="Add another reminder" resource-id="com.simplemobiletools.calendar.pro:id/event_reminder_2" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,1385][1080,1530]" />\r\n                <node index="13" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_reminder_divider" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1551][1080,1552]" />\r\n                <node index="14" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_repetition_image" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[32,1573][137,1698]" />\r\n                <node index="15" text="No repetition" resource-id="com.simplemobiletools.calendar.pro:id/event_repetition" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,1573][1080,1698]" />\r\n                <node index="16" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_repetition_divider" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1719][1080,1720]" />\r\n                <node index="17" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_caldav_calendar_divider" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1720][1080,1721]" />\r\n                <node index="18" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_type_image" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[32,1742][137,1794]" />\r\n                <node index="20" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_type_holder" class="android.widget.RelativeLayout" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[137,1742][1080,1794]">\r\n                  <node index="0" text="Regular event" resource-id="com.simplemobiletools.calendar.pro:id/event_type" class="android.widget.TextView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[148,1742][938,1794]" />\r\n                  <node index="1" text="" resource-id="com.simplemobiletools.calendar.pro:id/event_type_color" class="android.widget.ImageView" package="com.simplemobiletools.calendar.pro" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[959,1765][1038,1794]" />\r\n                </node>\r\n              </node>\r\n            </node>\r\n          </node>\r\n        </node>\r\n      </node>\r\n    </node>\r\n  </node>\r\n  <node index="0" text="" resource-id="com.android.systemui:id/navigation_bar_frame" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]">\r\n    <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]">\r\n      <node index="0" text="" resource-id="com.android.systemui:id/navigation_inflater" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]">\r\n        <node index="0" text="" resource-id="com.android.systemui:id/rot0" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]">\r\n          <node index="0" text="" resource-id="com.android.systemui:id/deadzone" class="android.view.View" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]" />\r\n          <node index="1" text="" resource-id="com.android.systemui:id/nav_buttons" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]">\r\n            <node index="0" text="" resource-id="com.android.systemui:id/center_group" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]">\r\n              <node index="0" text="" resource-id="com.android.systemui:id/home" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[435,1794][645,1920]">\r\n                <node index="0" text="" resource-id="com.android.systemui:id/home_button" class="android.widget.ImageView" package="com.android.systemui" content-desc="Home" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" visible-to-user="true" bounds="[435,1794][645,1920]" />\r\n                <node index="1" text="" resource-id="" class="android.widget.RelativeLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[435,1794][645,1920]" />\r\n                <node index="2" text="" resource-id="com.android.systemui:id/white" class="android.widget.ImageView" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[511,1828][569,1886]" />\r\n                <node index="3" text="" resource-id="com.android.systemui:id/white_cutout" class="android.widget.ImageView" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[511,1828][569,1886]" />\r\n              </node>\r\n            </node>\r\n            <node index="1" text="" resource-id="com.android.systemui:id/ends_group" class="android.widget.LinearLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[0,1794][1080,1920]">\r\n              <node index="0" text="" resource-id="com.android.systemui:id/back" class="android.widget.ImageView" package="com.android.systemui" content-desc="Back" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" visible-to-user="true" bounds="[131,1794][341,1920]" />\r\n              <node index="1" text="" resource-id="com.android.systemui:id/recent_apps" class="android.widget.ImageView" package="com.android.systemui" content-desc="Overview" checkable="false" checked="false" clickable="true" enabled="true" focusable="true" focused="false" scrollable="false" long-clickable="true" password="false" selected="false" visible-to-user="true" bounds="[739,1794][949,1920]" />\r\n              <node index="2" text="" resource-id="" class="android.widget.FrameLayout" package="com.android.systemui" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" focused="false" scrollable="false" long-clickable="false" password="false" selected="false" visible-to-user="true" bounds="[949,1794][1080,1920]" />\r\n            </node>\r\n          </node>\r\n        </node>\r\n      </node>\r\n    </node>\r\n  </node>\r\n</hierarchy>'
    root = et.fromstring(gui)
    Title = root.find(".//*[@text='Title']")

    data = {
        'selector': 'fill the task title',
        'action': 'set_text',
        'action_data': {
            'text': 'test create task'
        }
    }
    record = Record(data)
    repair = Repair('try_next')
    for node, confi in repair.select(gui, record):
        print(node.attrib, confi)
