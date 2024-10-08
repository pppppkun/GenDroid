class Widget:
    def __init__(self, d):
        self.class_ = d['class']
        self.content_desc = d['content-desc']
        self.resource_id = d['resource-id']
        self.text = d['text']
        self.hint = d['hint'] if 'hint' in d else ''
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
        if self.resource_id == '':
            return ''
        if 'android:id/' in self.resource_id:
            return self.resource_id
        if self.package not in self.resource_id:
            return self.package + ':id/' + self.resource_id
        else:
            return self.resource_id

    def to_selector(self):
        resource_id = self.get_resource_id()
        return {
            'resource-id': resource_id,
            'content-desc': self.content_desc,
            'text': self.text
        }

    def __str__(self):
        return self.resource_id + ' ' + self.content_desc + ' ' + self.text