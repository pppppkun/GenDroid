import pymongo
from collections import namedtuple

from typing import List

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = ''
gui_col = ''

GUI = namedtuple('GUI', ['rid', 'pre', 'post'])
Events = namedtuple('events', ['rid', 'event_series'])
Record = namedtuple('record', ['rid', 'description', 'event_series', 'widgets', 'pre_device_info', 'post_device_info'
    , 'pre_screenshot', 'post_screenshot'])
Event = namedtuple('event', ['widget', 'action'])
records = list(Record)
event_segments = list(Events)
guis = list(GUI)
descriptions = list(str)
events = list(Event)


# d['description'] = description
# d['event_series'] = event_series
# d['widgets'] = widgets
# d['pre_device_info'] = pre_device_info
# d['post_device_info'] = post_device_info
# d['pre_screenshot'] = pre_screenshot
# d['post_screenshot'] = post_screenshot


def insert_record(record):
    rid = len(records)
    records.append(Record(rid, **record))
    event_segments.append(Events(rid, record['event_series']))
    guis.append(GUI(rid=rid, pre=record['pre_screenshot'], post=record['post_screenshot']))
    descriptions.append(record['description'])
    for e_w in list(zip(record['event_series'], record['widgets'])):
        event = e_w[0]
        widget = e_w[1]
        action = event['action']
        events.append(Event(action=action, widget=widget))


def get_all_events() -> List[Event]:
    return events
