import pymongo
from collections import namedtuple

from typing import List

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = ''
gui_col = ''

GUI = namedtuple('GUI', ['rid', 'pre_img', 'post_img', 'pre_xml', 'post_xml'])
Events = namedtuple('events', ['rid', 'event_series'])
Record = namedtuple('record', ['rid', 'description', 'event_series', 'widgets', 'pre_device_info', 'post_device_info'
    , 'pre_screenshot', 'post_screenshot', 'pre_xml', 'post_xml'])
Event = namedtuple('event', ['widget', 'action'])
records = list()
event_segments = list()
guis = list()
descriptions = list()
events = list()


def insert_record(record):
    rid = len(records)
    records.append(Record(rid, **record))
    event_segments.append(Events(rid, record['event_series']))
    guis.append(GUI(rid=rid, pre_img=record['pre_screenshot'], post_img=record['post_screenshot']
                    , pre_xml=record['pre_xml'], post_xml=record['post_xml']))
    descriptions.append(record['description'])
    for e_w in list(zip(record['event_series'], record['widgets'])):
        event = e_w[0]
        widget = e_w[1]
        action = event['action']
        events.append(Event(action=action, widget=widget))


def get_all_events() -> List[Event]:
    return events


def get_all_guis() -> List[GUI]:
    return guis
