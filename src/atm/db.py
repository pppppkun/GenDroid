import os.path
from bidict import bidict
from collections import defaultdict, namedtuple
import xml.etree.ElementTree as et

StringInfo = namedtuple('string_info', ['text', 'id'])


class DataBase:
    def __init__(self, decompile_folder, package):
        self.decompile_folder = decompile_folder
        self.widgets = defaultdict(list)
        self.widget_bidict = bidict()
        self.strings = dict(StringInfo)
        self.extract_widget()
        self.extract_strings()
        self.package = package

    # def extract_widgets_from_layout(self):
    #     parent_layout = {}
    #     layout_folder = os.path.join(self.decompile_folder, 'res', 'layout')
    #     layout_xmls = [f for f in os.listdir(layout_folder)
    #                    if os.path.isfile(os.path.join(layout_folder, f)) and f.endswith('.xml')]
    #     # first pass to get layout hierarchy
    #     for xml_file in layout_xmls:
    #         current_layout = xml_file.split('.')[0]
    #         e = et.parse(os.path.join(layout_folder, xml_file))
    #         for node in e.findall('//include'):  # e.g., <include layout="@layout/content_main" />
    #             child_layout = self.decode(node.attrib['layout'])
    #             parent_layout[child_layout] = current_layout
    #
    #     # second pass to get widgets from a layout
    #     # android.widget.ImageButton
    #
    #     attrs = ['id', 'text', 'contentDescription', 'hint']
    #     attrs_ui = ['resource-id', 'text', 'content-desc', 'text']  # the attributes interpreted by UI Automator
    #     widgets = []
    #     for xml_file in layout_xmls:
    #         # print(xml_file)
    #         current_layout = xml_file.split('.')[0]
    #         e = et.parse(os.path.join(layout_folder, xml_file))
    #         for w_type in ResourceParser.WIDGET_TYPES_FOR_LAYOUT:
    #             for node in e.xpath('//' + w_type):
    #                 d = {}
    #                 for k, v in node.attrib.items():
    #                     # attrib: {http://schemas.android.com/apk/res/android}id, @id/ok
    #                     for a in attrs:
    #                         k = k.split('}')[1] if k.startswith('{') else k
    #                         if k == a:
    #                             a_ui = attrs_ui[attrs.index(a)]
    #                             if a_ui in d:
    #                                 d[a_ui] += self.decode(v)
    #                             else:
    #                                 d[a_ui] = self.decode(v)
    #                             # d[a] = v
    #                 if d:
    #                     d['class'] = w_type
    #                     # FloatingActionButton will appear as ImageButton when interpreted by UI Automator
    #                     if d['class'] == 'android.support.design.widget.FloatingActionButton':
    #                         d['class'] = 'ImageButton'
    #                     d['class'] = ResourceParser.CLASS_PREFIX + d['class']
    #                     if 'resource-id' in d:
    #                         d['oId'] = self.get_oId_from_wName(d['resource-id'])
    #                     else:
    #                         d['oId'] = ""
    #                     mother_layout = current_layout
    #                     while mother_layout in parent_layout:
    #                         mother_layout = parent_layout[mother_layout]
    #                     d['layout_name'] = mother_layout
    #                     d['layout_oId'] = self.get_oId_from_lName(mother_layout)
    #                     d['package'], d['activity'], d['method'] = self.match_act_info_for_oId(d['oId'],
    #                                                                                            d['layout_oId'])
    #                     for a in attrs_ui:
    #                         if a not in d:
    #                             d[a] = ""
    #                     # if d['name'] or d['oId']:
    #                     widgets.append(d)
    #                     # print(d)
    #     return widgets

    def extract_widget(self):
        name_id_map = dict()
        tree = et.parse(os.path.join(self.decompile_folder, 'res', 'values', 'public.xml'))
        for node in tree.findall('.//resources/public/[@type="id"]'):
            if 'name' in node.attrib and 'id' in node.attrib:
                name = node.attrib['name']
                id = str(int(node.attrib['id'], 16))
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

    # def get_all_widget(self):


if __name__ == '__main__':
    db = DataBase('/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark/todo/decompile', '1')
    print(db.strings['abc_action_bar_home_description'].text)

