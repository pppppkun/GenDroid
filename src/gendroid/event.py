from collections import namedtuple
from gendroid.utils import calculation_position

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
INTENT_EVENT = 'intent'
CLICK_WITH_POS = 'click_with_pos'

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

NON_SELECTOR_EVENTS = {
    'swipe',
    'scroll',
    'intent',
    'click_with_pos'
}

event_factory = {
    **{KEY_EVENT: lambda event_data: Event(event_data.action) for KEY_EVENT in KEY_EVENTS},
    CLICK_EVENT: lambda event_data: Event(CLICK_EVENT, selector=event_data.selector),
    CLICK_WITH_POS: lambda event_data: Event(CLICK_WITH_POS, position=event_data.data['position']),
    LONG_CLICK_EVENT: lambda event_data: Event(LONG_CLICK_EVENT, selector=event_data.selector),
    SET_TEXT_EVENT: lambda event_data: Event(SET_TEXT_EVENT, selector=event_data.selector,
                                             text=event_data.data['text']),
    CHECK_CLICK_EVENT: lambda event_data: Event(CHECK_CLICK_EVENT, selector=event_data.selector),
    TOUCH_EVENT: lambda event_data: Event(event_data.action, selector=event_data.selector),
    # SWIPE_EVENT: lambda event_data: Event(event_data.action, selector=event_data.selector,
    #                                   direction=event_data.action_data['direction']),
    SCROLL_EVENT: lambda event_data: Event(event_data.action, direction=event_data.data['direction']),
    INTENT_EVENT: lambda event_data: Event(event_data.action, intent=event_data.data['intent'])
}


def scroll_based_direction(device, event):
    if event.direction.lower() == 'down':
        device.u(scrollable=True).scroll.toEnd()
    if event.direction.lower() == 'up':
        device.u(scrollable=True).scroll.toBeginning()
    device.u.sleep(2)


def click_using_position(device, event):
    position = event.position
    x, y = calculation_position(position)
    device.u.click(x, y)
    device.u.sleep(2)


send_event_to_device = {
    **{KEY_EVENT: lambda device, event: device.u.keyevent(event.action) for KEY_EVENT in KEY_EVENTS},
    CLICK_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    CLICK_WITH_POS: lambda device, event: click_using_position(device, event),
    LONG_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).long_click(),
    SET_TEXT_EVENT: lambda device, event: device.select_widget(event.selector).set_text(event.text),
    CHECK_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    DRAG_EVENT: lambda device, event: device.select_widget(event.selector).drag_to(event.drag, event.duration),
    TOUCH_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    # SWIPE_EVENT: lambda device, event: device.u.swipe(1000, 1000, 300, 300),
    SCROLL_EVENT: lambda device, event: scroll_based_direction(device, event),
    INTENT_EVENT: lambda device, event: device.u.shell(event.intent)

    # DOUBLE_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).double_click()
}


def build_event(action, selector, data=None):
    event_data = EventData(action=action, selector=selector, data=data)
    event = event_factory[action](event_data)
    return event


class Event:
    def __init__(self, action, **kwargs):
        self.text = None
        self.intent = None
        self.action = action
        self.selector = None
        self.confidence = -1
        self.position = None
        self.direction = None
        for i in kwargs:
            self.__setattr__(i, kwargs[i])

    def __str__(self):
        return f'Event action={self.action}, selector={self.selector} confidence={self.confidence}'

    def event_str(self):
        return f'ACTION[{self.action}]SELECTOR[{self.selector}]DATA[{self.text}]'

    def to_dict(self):
        return {'action': self.action, 'selector': self.selector, 'data': self.text}

    def to_uiautomator2_format(self):
        if not self.selector:
            if self.action == 'click_with_pos':
                x, y = calculation_position(self.position)
                return f'd.click({x}, {y})'
            if self.action == 'scroll':
                if self.direction.lower() == 'down':
                    return f'd(scrollable=True).scroll.toEnd()'
                if self.direction.lower() == 'up':
                    return f'd(scrollable=True).scroll.toBeginning()'
            if self.action == 'intent':
                return f'd.shell({repr(self.intent)})'
            return f'd.keyevent(\'{self.action}\')'

        translate = {
            'text': 'text',
            'content-desc': 'descriptionContains',
            'index': 'index',
            'resource-id': 'resourceId',
            'class': 'className'
        }
        temp = {}
        for x in translate:
            if x in self.selector and self.selector[x]:
                temp[translate[x]] = self.selector[x]
        # temp = dict(map(lambda x: (translate[x], self.selector[x]), self.selector))
        param = []
        if self.action != 'set_text':
            for key in temp:
                param.append(f'{key}={repr(temp[key])}')
            return 'd({}).{}()'.format(','.join(param), self.action)
        else:
            # if 'text' in temp:
            #     temp.pop('text')
            for key in temp:
                if 'text' == key:
                    continue
                param.append(f'{key}={repr(temp[key])}')
            if len(param) == 0:
                param.append(f'text={repr(temp["text"])}')
            return 'd({}).{}(\'{}\')'.format(','.join(param), self.action, self.text)


class VirtualEvent:
    def __init__(self, description, data):
        self.description = description
        self.data = data


if __name__ == '__main__':
    # e = Event('click', text='123', location=123)
    # print(e.text)
    print(event_factory)
