from collections import namedtuple

EventData = namedtuple('EventData', ['action', 'selector', 'data'])
CLICK_EVENT = 'click'
LONG_CLICK_EVENT = 'long_click'
DOUBLE_CLICK_EVENT = 'double_click'
SET_TEXT_EVENT = 'set_text'
DRAG_EVENT = 'drag_to'
TOUCH_EVENT = 'touch'
CHECK_CLICK_EVENT = 'check'
SWIPE_EVENT = 'swipe'
SCROLL_EVENT = 'scroll'
SCROLL_EVENT_TO_END = 'scroll_end'

KEY_EVENTS = {
    'home',
    'back',
    'left',
    'right',
    'up',
    'down',
    'center',
    'menu',
    'volume_up',
    'volume_down',
    'volume_mute',
    'power'
}

event_factory = {
    **{KEY_EVENT: lambda event_data: Event(event_data.action) for KEY_EVENT in KEY_EVENTS},
    CLICK_EVENT: lambda event_data: Event(CLICK_EVENT, selector=event_data.selector),
    LONG_CLICK_EVENT: lambda event_data: Event(LONG_CLICK_EVENT, selector=event_data.selector),
    SET_TEXT_EVENT: lambda event_data: Event(SET_TEXT_EVENT, selector=event_data.selector,
                                             text=event_data.data['text']),
    CHECK_CLICK_EVENT: lambda event_data: Event(CHECK_CLICK_EVENT, selector=event_data.selector),
    TOUCH_EVENT: lambda event_data: Event(event_data.action, selector=event_data.selector),
    # SWIPE_EVENT: lambda event_data: Event(event_data.action, selector=event_data.selector,
    #                                   direction=event_data.action_data['direction']),
    SCROLL_EVENT: lambda event_data: Event(event_data.action, direction=event_data.data['direction'])
}


def scroll_based_direction(device, event):
    if event.direction == 'end':
        device.u(scrollable=True).scroll.toEnd()
    if event.direction == 'beginning':
        device.u(scrollable=True).scroll.toBeginning()


send_event_to_device = {
    **{KEY_EVENT: lambda device, event: device.u.keyevent(event.action) for KEY_EVENT in KEY_EVENTS},
    CLICK_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    LONG_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).long_click(),
    SET_TEXT_EVENT: lambda device, event: device.select_widget(event.selector).set_text(event.text),
    CHECK_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    DRAG_EVENT: lambda device, event: device.select_widget(event.selector).drag_to(event.drag, event.duration),
    TOUCH_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    # SWIPE_EVENT: lambda device, event: device.u.swipe(1000, 1000, 300, 300),
    SCROLL_EVENT: lambda device, event: scroll_based_direction(device, event)

    # DOUBLE_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).double_click()
}


def build_event(action, selector, data=None):
    event_data = EventData(action=action, selector=selector, data=data)
    event = event_factory[action](event_data)
    return event


class Event:
    def __init__(self, action, **kwargs):
        self.text = None
        self.action = action
        self.selector = None
        self.confidence = -1
        for i in kwargs:
            self.__setattr__(i, kwargs[i])

    def __str__(self):
        return f'Event action={self.action}, selector={self.selector} confidence={self.confidence}'

    def to_dict(self):
        return {'action': self.action, 'selector': self.selector, 'data': self.text}

    def to_uiautomator2_format(self):
        translate = {
            'text': 'text',
            'content-desc': 'descriptionContains',
            'index': 'index',
            'resource-id': 'resourceId',
            'class': 'className'
        }
        temp = dict(map(lambda x: (translate[x], self.selector[x]), self.selector))
        param = []
        for key in temp:
            param.append(f'{key}=\'{temp[key]}\'')
        if self.action != 'set_text':
            return 'd({}).{}()'.format(','.join(param), self.action)
        else:
            return 'd({}).{}(\'{}\')'.format(','.join(param), self.action, self.text)


class VirtualEvent:
    def __init__(self, description, data):
        self.description = description
        self.data = data


if __name__ == '__main__':
    # e = Event('click', text='123', location=123)
    # print(e.text)
    print(event_factory)
