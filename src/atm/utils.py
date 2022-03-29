import xml.etree.ElementTree as et


class FunctionWrap:
    def __init__(self, _data, f=None, _lambda=None):
        self.data = _data
        if f is None:
            self.f = None
        else:
            self.f = f(_lambda, _data)

    def append(self, f, _lambda):
        if self.f is None:
            self.f = f(_lambda, self.data)
        elif f is sorted:
            self.f = sorted(self.f, key=_lambda)
        else:
            self.f = f(_lambda, self.f)
        return self

    def iter(self):
        return self.f

    def do(self):
        if type(self.f) is not filter and type(self.f) is not map:
            return self.f
        else:
            return list(self.f)


def get_class(node):
    class_ = ''
    if type(node) is dict:
        if 'class' in node:
            class_ = node['class']
        if 'className' in node:
            class_ = node['className']
    if type(node) is et:
        class_ = node.get('class')
    class_ = class_[class_.rfind('.') + 1:]
    return class_


attributes_map = {
    'text': 'text',
    'contentDescription': 'content-desc',
    'resourceName': 'resource-id',
    'className': 'class'
}


def is_same_widget_from_widget_info(w1, w2):
    is_same = True
    if 'content-desc' in w2:
        w3 = w1
        w1 = w2
        w2 = w3
    # Exactly the same
    for attr in attributes_map:
        a1 = attr
        a2 = attributes_map[a1]
        is_same = is_same and w1[a2] == w2[a1]

    return is_same


def get_all_nodes(xml):
    result = []

    def get_child(root):
        for i in root:
            result.append(i)
            get_child(i)

    get_child(xml)
    return result


FEATURE_KEYS = ['class', 'resource-id', 'text', 'content-desc', 'clickable', 'password', 'naf']
IRRELEVANT_WORDS = ['bt', 'et', 'tv', 'fab', 'rv', 'cb', 'ac']


def get_activity(node):
    assert node.split(':')[0]
    return node.split(':')[0].split('$')[0]


def get_method(node):
    assert node.split()[-1].split('(')[0]
    return node.split()[-1].split('(')[0]


def get_selector_from_dynamic_edge(criteria):
    attributes = ['text', 'content-desc', 'resource-id']
    selectors = dict()
    for attribute in attributes:
        assert attribute in criteria
        selectors[attribute] = criteria[attribute]
    return selectors
