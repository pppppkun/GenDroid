import os
from xml.etree import ElementTree as et
from demo.event import Event


def bounds2list(bounds):
    s = bounds
    s = '[' + s + ']'
    s = s[:s.find(']') + 1] + ',' + s[s.find(']') + 1:]
    return eval(s)


def gui_xml2json_helper(node):
    children = []
    d_ = node.attrib
    for child in node:
        children.append(gui_xml2json_helper(child))
    d_['children'] = children
    if 'bounds' not in d_:
        d_['bounds'] = None
    else:
        bounds = bounds2list(d_['bounds'])
        d_['bounds'] = [
            bounds[0][0],
            bounds[1][0],
            bounds[0][1],
            bounds[1][1]
        ]
    return d_


def gui_xml2json(xml: et, activity_name):
    root = et.fromstring(xml)
    d = gui_xml2json_helper(root)
    result = {
        'activity_name': activity_name,
        'is_keyboard_deployed': False, 'activity': {'root': d}}
    # f = open('calendar.json', 'w+')
    # json.dump(result, f, indent=4)
    return result


def gui_similarity_matrix(record):
    pass


def to_scripts():
    scripts = """
import uiautomator2 as u2
d = u2.connect()
"""
    event = Event(action='click', selector={'text':'123', 'content-desc':'licas', 'resource-id':'aljchas'})
    print(event.to_uiautomator2_format())


if __name__ == '__main__':
    to_scripts()
