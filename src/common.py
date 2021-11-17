import os
from constant import HTML_ENTIRY
class Data:
    def __init__(self, label, text_a, text_b) -> None:
        self.label = label
        self.text_a = text_a
        self.text_b = text_b
    def __hash__(self) -> int:
        return hash(self.label + self.text_a + self.text_b)
    def __eq__(self, o: object) -> bool:
        return self.to_text() == o.to_text() 
    def to_text(self):
        return self.label + '\t' + self.text_a + '\t' + self.text_b
    def __str__(self) -> str:
        return self.to_text()
    def __repr__(self):
        return '<Data {}>'.format(self.to_text())

class DataSet:
    def __init__(self, is_remove_duplicate) -> None:
        self.is_remove_duplicate = is_remove_duplicate
        self.container = set() if is_remove_duplicate else list()

    def add(self, data):
        if self.is_remove_duplicate:
            self.container.add(data)
        else:
            self.container.append(data)   

    def to_set(self):
        return set(self.container)

    def to_list(self):
        return list(self.container) 

    def union(self, data_set):
        if self.is_remove_duplicate:
            self.container.union(data_set.to_set())
        else:
            self.container.extend(data_set.to_list())    
    
    def over_sampling():
        return DataSet(is_remove_duplicate=False)
    
    def under_sampling():
        return DataSet(is_remove_duplicate=False)


def files(log):
    for path, __, files in os.walk(log):
        for file in files:
            if file.endswith('.json') and 'result' in file:
                yield os.path.join(path, file) 
                # res = json_file_process(
                #     os.path.join(path, file),  is_train_set)
                # yield res, path, file

def translate_html_entity(text):
    for key in HTML_ENTIRY:
        if key in text:
            text = text.replace(key, HTML_ENTIRY[key])
    return text