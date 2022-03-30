class Widget:
    def __init__(self, d):
        self.class_ = d['class']
        self.content_desc = d['content-desc']
        self.resource_id = d['resource-id']
        self.text = d['text']
        self.activity = d['hint'] if 'hint' in d else None
        self.activity = d['activity'] if 'activity' in d else None
        self.package = d['package']
        # different with resource-id.
        # self.id is Integer.
        self.id = d['id'] if 'id' in d else None
        self.sibling_widget = None
        self.parent_widget = None
        self.neighbor_widget = None

    def get_class(self):
        return self.class_

    def get_resource_id(self):
        return self.package + self.resource_id

    def to_selector(self):
        return {
            'resource-id': self.resource_id,
            'content-desc': self.content_desc,
            'text': self.text
        }
