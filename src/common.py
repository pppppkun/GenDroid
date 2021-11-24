import os
from constant import HTML_ENTIRY


def files(log):
    for path, __, files_ in os.walk(log):
        for file in files_:
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


def translate_seria_text_to_english(seria):
    import six
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()
    result = dict()
    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    count = 0
    for data in seria:
        result[data] = translate_client.translate(
            data, target_language='en')['translatedText']
        result[data] = translate_html_entity(result[data])
        count += 1
        if count % 200 == 0:
            print(count)
            print(len(result))
    return result


