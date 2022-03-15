from demo.event import event_factory, VirtualEvent, EventData
from demo.record import record_events
from scripts.convert import gui_xml2json
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
