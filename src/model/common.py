import os
from constant import HTML_ENTIRY

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