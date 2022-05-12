import os.path
from bidict import bidict
from collections import defaultdict, namedtuple
import xml.etree.ElementTree as et
from genDroid.widget import Widget
from genDroid.utils import IRRELEVANT_WORDS
import csv

StringInfo = namedtuple('string_info', ['text', 'id'])

WIDGET_TYPES_FOR_LAYOUT = ['TextView', 'EditText', 'Button', 'ImageButton',
                           'android.support.design.widget.FloatingActionButton',
                           'CheckBox', 'RadioButton']  # ,


# 'CheckBox', 'Switch', 'RadioButton']

class DataBase:
    def __init__(self, decompile_folder, atm_folder, package):
        self.package = package
        self.atm_folder = atm_folder
        self.decompile_folder = decompile_folder
        self.widgets = list()
        self.widget_bidict = None
        self.layout_bidict = None
        self.strings = defaultdict(StringInfo)
        self.extract_widget()
        self.extract_layout()
        self.extract_strings()
        # self.cid2activity = self.extract_activity()
        self.extract_widgets_from_layout()

    def extract_widgets_from_layout(self):
        parent_layout = {}
        layout_folder = os.path.join(self.decompile_folder, 'res', 'layout')
        layout_xmls = [f for f in os.listdir(layout_folder)
                       if os.path.isfile(os.path.join(layout_folder, f)) and f.endswith('.xml')]
        # first pass to get layout hierarchy
        for xml_file in layout_xmls:
            current_layout = xml_file.split('.')[0]
            e = et.parse(os.path.join(layout_folder, xml_file)).getroot()
            for node in e.findall('.//include'):  # e.g., <include layout="@layout/content_main" />
                child_layout = self.decode(node.attrib['layout'])
                parent_layout[child_layout] = current_layout

        # second pass to get widgets from a layout
        # android.widget.ImageButton
        has_seen = {}
        attrs = ['id', 'text', 'contentDescription', 'hint']
        attrs_ui = ['resource-id', 'text', 'content-desc', 'hint']  # the attributes interpreted by UI Automator
        widget_str_set = set()
        for xml_file in layout_xmls:
            current_layout = xml_file.split('.')[0]
            e = et.parse(os.path.join(layout_folder, xml_file)).getroot()
            for w_type in WIDGET_TYPES_FOR_LAYOUT:
                for node in e.findall('.//' + w_type):
                    d = {}
                    for key in node.attrib:
                        value = node.attrib[key]
                        if 'schemas.android.com' in key:
                            key = key.split('}')[1]
                        if key in attrs:
                            key = attrs_ui[attrs.index(key)]
                        if key in d:
                            d[key] += ',' + self.decode(value)
                        else:
                            d[key] = self.decode(value)
                        d['package'] = self.package
                    if d:
                        d['class'] = w_type
                        if 'FloatingActionButton' in d['class']:
                            d['class'] = 'ImageButton'
                        d['class'] = 'android.widget.' + d['class']
                        if 'resource-id' in d:
                            d['id'] = self.get_widget_id_from_name(d['resource-id'])
                        else:
                            d['id'] = ""
                        mother_layout = current_layout
                        while mother_layout in parent_layout:
                            mother_layout = parent_layout[mother_layout]
                        # d['layout_name'] = mother_layout
                        # d['layout_oId'] = self.get_layout_id_from_name(mother_layout)
                        # d['package'], d['activity'], d['method'] = self.match_act_info_for_oId(d['id'], d['layout_oId'])
                        for attr in attrs_ui:
                            if attr not in d:
                                d[attr] = ''
                        try:
                            s = d['resource-id'] + d['id']
                            if s not in widget_str_set:
                                widget_str_set.add(s)
                                self.widgets.append(Widget(d))
                        except TypeError:
                            self.widgets.append(Widget(d))
                            pass
                            # dynamic widget without id
                            # print(d)

    def extract_layout(self):
        name_id_map = dict()
        e = et.parse(os.path.join(self.decompile_folder, 'res', 'values', 'public.xml')).getroot()
        for node in e.findall('.//public[@type="layout"]'):
            if 'name' in node.attrib and 'id' in node.attrib:
                name = node.attrib['name']
                id = str(int(node.attrib['id'], 16))
                assert name not in name_id_map
                name_id_map[name] = id
        self.layout_bidict = bidict(name_id_map)

    def match_act_info_for_oId(self, widget_id, layout_id):
        act_from_w, act_from_l = self.get_activity_from_cid(widget_id), self.get_activity_from_cid(
            layout_id)
        if act_from_w and act_from_l:
            activity_w = act_from_w['activity'].split('$')[0]
            activity_l = act_from_l['activity'].split('$')[0]
            if activity_w != activity_l:
                if 'activity' in activity_w.lower():
                    return list(act_from_w.values())
                elif 'activity' in activity_l.lower():
                    return list(act_from_l.values())
                else:
                    assert False
            return list(act_from_w.values())
        elif act_from_w or act_from_l:
            if act_from_w:
                return list(act_from_w.values())
            else:
                return list(act_from_l.values())
        else:
            return "", "", ""

    def extract_activity(self):
        cid2activity = {}
        with open(os.path.join(self.atm_folder, 'constantInfo.csv')) as f:
            # fields: constantId, packageIn, methodIn, methodRefClass, methodRef, codeUnit,
            # (varName, varClass, varRefClass)
            reader = csv.DictReader(f)
            for row in reader:
                oId = row['constantId']
                if row['packageIn'].startswith(self.package) and \
                        (oId in self.widget_bidict.inverse or oId in self.layout_bidict.inverse):
                    cid2activity[oId] = {'package': self.package,
                                         'activity': row['packageIn'].replace(self.package, ''),
                                         'method': row['methodIn']}
        return cid2activity

    def extract_widget(self):
        name_id_map = dict()
        tree = et.parse(os.path.join(self.decompile_folder, 'res', 'values', 'public.xml')).getroot()
        for node in tree.findall('.//public/[@type="id"]'):
            if 'name' in node.attrib and 'id' in node.attrib:
                name = node.attrib['name']
                id = str(int(node.attrib['id'], 16))
                assert name not in name_id_map
                name_id_map[name] = id
        self.widget_bidict = bidict(name_id_map)

    def extract_strings(self):
        name_text_map = dict()
        # e.g., <string name="character_counter_pattern">%1$d / %2$d</string>
        #       <item type="string" name="mdtp_ampm_circle_radius_multiplier">0.22</item>
        e = et.parse(os.path.join(self.decompile_folder, 'res', 'values', 'strings.xml')).getroot()
        for node in e.findall('string'):
            if 'name' in node.attrib:
                name = node.attrib['name']
                text = node.text
                name_text_map[name] = text
        for node in e.findall('item'):
            if 'name' in node.attrib and 'type' in node.attrib and node.attrib['type'] == 'string':
                name = node.attrib['name']
                text = node.text
                name_text_map[name] = text
        name_id_map = dict()
        e = et.parse(os.path.join(self.decompile_folder, 'res', 'values', 'public.xml'))
        for node in e.findall('.//public[@type="string"]'):
            if 'name' in node.attrib and 'id' in node.attrib:
                sName = node.attrib['name']
                oId = str(int(node.attrib['id'], 16))
                assert sName not in name_id_map
                name_id_map[sName] = oId
        invalid_keys = set(name_id_map.keys()).difference(set(name_text_map.keys()))  # strings without text
        for k in invalid_keys:
            name_id_map.pop(k)
        assert set(name_id_map.keys()) == set(name_text_map.keys())
        for name in name_id_map.keys():
            id = name_id_map[name]
            text = name_text_map[name]
            string_info = StringInfo(text=text, id=id)
            self.strings[name] = string_info

    def decode(self, value):
        if not value.startswith('@'):
            return value
        if value.startswith('@id'):  # e.g,. @id/newShortcut
            return value.split('/')[-1]
        if value.startswith('@layout'):  # e.g,. @layout/content_main
            return value.split('/')[-1]
        if value.startswith('@string'):
            sName = value.split('/')[-1]
            # print(value, sName, self.sName_to_info.keys())
            if sName in self.strings:
                return self.strings[sName].text
            else:
                return sName
        if value.startswith('@android:string'):  # e.g., @android:string/cancel
            return value.split('/')[-1]
        if value.startswith('@android:id'):  # e.g., @android:id/button3
            return value.split('/')[-1]
        return value

    def get_action_from_history(self, clazz):
        pass

    def get_widget_id_from_name(self, w_name):
        w_name = self.decode(w_name)
        if w_name in self.widget_bidict:
            return self.widget_bidict[w_name]
        return ""

    def get_widget_name_from_id(self, w_id):
        if w_id in self.widget_bidict.inverse:
            return self.widget_bidict.inverse[w_id]
        return None

    def get_layout_id_from_name(self, name):
        name = self.decode(name)
        if name in self.layout_bidict:
            return self.layout_bidict[name]
        else:
            return None

    def get_activity_from_cid(self, cid):
        if cid in self.cid2activity:
            return self.cid2activity[cid]
        else:
            return None

    def update_widget(self, widget, activity):
        is_in = False
        for w in self.widgets:
            if w == widget:
                is_in = True
                if w.activity == '':
                    w.activity = activity
        if not is_in:
            self.widgets.append(widget)

    def update_by_activity(self):
        pass

    def get_all_widgets(self):
        result = []
        for widget in self.widgets:
            if widget.activity != '' and widget.activity is not None:
                result.append(widget)
        return result

    def get_origin_widget_text(self, rid):
        for widget in self.widgets:
            if widget.get_resource_id() == rid:
                return widget
        return None


if __name__ == '__main__':
    db = DataBase('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/todo/decompile',
                  '/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/todo/out',
                  'com.simplemobiletools.calendar.pro')
    n = 0
    atm = open('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/todo/out/atm.gv', 'r').read()
    # '2131296532'
    for widget in db.widgets:
        if 'EditText' in widget.get_class():
            print(widget.resource_id, widget.hint)
