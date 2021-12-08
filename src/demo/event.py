KEY_EVENT = 'key'
CLICK_EVENT = 'click'
LONG_CLICK_EVENT = 'long_click'
DOUBLE_CLICK_EVENT = 'double_click'
SET_TEXT_EVENT = 'set_text'
DRAG_EVENT = 'drag_to',
TOUCH_EVENT = 'touch'

event_action_lambda_map = {
    KEY_EVENT: lambda device, event: device.keyevent(event.key),
    CLICK_EVENT: lambda device, event: device.select_widget(event.selector).click(),
    LONG_CLICK_EVENT: lambda device, event: device.select_widget(event.selector).long_click(),
    SET_TEXT_EVENT: lambda device, event: device.select_widget(event.selector).set_text(event.text),
    DRAG_EVENT: lambda device, event: device.select_widget(event.selector).drag_to(event.drag, event.duration)
}


class Event:
    def __init__(self, action, selector, **kwargs):
        self.action = action
        self.selector = selector
        for i in kwargs:
            self.__setattr__(i, kwargs[i])


if __name__ == '__main__':
    e = Event('click', {'a': 1}, text='123', location=123)
