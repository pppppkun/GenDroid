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

event_init_map = {
    **{KEY_EVENT: lambda record: Event(record.action) for KEY_EVENT in KEY_EVENTS},
    CLICK_EVENT: lambda record: Event(record.action, selector=record.selector),
    LONG_CLICK_EVENT: lambda record: Event(record.action, selector=record.selector),
    SET_TEXT_EVENT: lambda record: Event(record.action, selector=record.selector, text=record.action_data['text']),
    CHECK_CLICK_EVENT: lambda record: Event(record.action, selector=record.selector),
    TOUCH_EVENT: lambda record: Event(record.action, selector=record.selector),
    # SWIPE_EVENT: lambda record: Event(record.action, selector=record.selector,
    #                                   direction=record.action_data['direction']),
    SCROLL_EVENT: lambda record: Event(record.action, direction=record.action_data['direction'])
}


def scroll_based_direction(device, event):
    if event.direction == 'end':
        device.u(scrollable=True).scroll.toEnd()
    if event.direction == 'beginning':
        device.u(scrollable=True).scroll.toBeginning()


event_action_lambda_map = {
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


class Event:
    def __init__(self, action, **kwargs):
        self.action = action
        self.selector = None
        self.confidence = None
        # self.action_data = None
        for i in kwargs:
            self.__setattr__(i, kwargs[i])
        # if self.action == SCROLL_EVENT:

    def __str__(self):
        return 'Event action={action}, selector={selector}'.format(action=self.action, selector=self.selector)


if __name__ == '__main__':
    # e = Event('click', text='123', location=123)
    # print(e.text)
    print(event_init_map)
