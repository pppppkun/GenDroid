CLICK_EVENT = 'click'
LONG_CLICK_EVENT = 'long_click'
DOUBLE_CLICK_EVENT = 'double_click'
SET_TEXT_EVENT = 'set_text'
DRAG_EVENT = 'drag_to'
TOUCH_EVENT = 'touch'
CHECK_CLICK_EVENT = 'check'

SET_ACTIONS = {
    'enter',
    'input'
}

ACTIONS = {
    CLICK_EVENT,
    LONG_CLICK_EVENT,
    DOUBLE_CLICK_EVENT,
    DRAG_EVENT,
    TOUCH_EVENT,
    CHECK_CLICK_EVENT,
    'enter',
    'input'
}

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
    # KEY_EVENT: lambda record: Event(record.action),
    **{KEY_EVENT: lambda record: Event(record.action) for KEY_EVENT in KEY_EVENTS},
    CLICK_EVENT: lambda record: Event(record.action, selector=record.selector),
    LONG_CLICK_EVENT: lambda record: Event(record.action, selector=record.selector),
    SET_TEXT_EVENT: lambda record: Event(record.action, selector=record.selector, text=record.action_data['text']),
    CHECK_CLICK_EVENT: lambda record: Event(record.action, selector=record.selector)
}

event_action_lambda_map = {
    **{KEY_EVENT: lambda device, event: device.u.keyevent(event.action) for KEY_EVENT in KEY_EVENTS},
    CLICK_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    LONG_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).long_click(),
    SET_TEXT_EVENT: lambda device, event: device.select_widget(event.selector).set_text(event.text),
    CHECK_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    DRAG_EVENT: lambda device, event: device.select_widget(event.selector).drag_to(event.drag, event.duration)
}


class Event:
    def __init__(self, action, **kwargs):
        self.action = action
        for i in kwargs:
            self.__setattr__(i, kwargs[i])

    def __str__(self):
        return 'Event action={action}, selector={selector}'.format(action=self.action, selector=self.selector)


EVENT_BACK = Event(action='back')

if __name__ == '__main__':
    # e = Event('click', text='123', location=123)
    # print(e.text)
    print(event_init_map)
