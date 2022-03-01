from demo.event import event_factory, VirtualEvent, EventData
from demo.record import record_events
import time


def get_info_and_screenshot(device):
    import os
    return device.u.app_current(), device.u.screenshot(os.path.join('img', str(int(time.time())) + '.jpg'))


def build_event(selector, action, data=None):
    # e_data = {'selector': selector, 'action': action}
    # if action_data:
    #     e_data['action_data'] = action_data
    e_data = EventData(action=action, selector=selector, data=data)
    return event_factory[e_data.action](e_data)


def execute_and_record(description_, events, device, executor):
    pre_info, pre_screenshot = get_info_and_screenshot(device)
    device.u.sleep(2)
    widgets = []
    events_ = []
    for event in events:
        widgets.append(device.select_widget(event.selector).info)
        events_.append(event.to_dict())
        executor.direct_execute(event)
    device.u.sleep(2)
    post_info, post_screenshot = get_info_and_screenshot(device)
    record_events(
        description=description_,
        event_series=events_,
        widgets=widgets,
        pre_screenshot=pre_screenshot,
        pre_device_info=pre_info,
        post_screenshot=post_screenshot,
        post_device_info=post_info
    )


def build_virtual_event(description_, data=None):
    return VirtualEvent(description_, data)
