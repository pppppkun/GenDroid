import os
from pandas.plotting import table
import matplotlib.pyplot as plt
from utils.constant import HTML_ENTITY

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 显示中文字体


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


def files(log):
    for path, __, files_ in os.walk(log):
        for file in files_:
            if file.endswith('.json') and 'result' in file:
                yield os.path.join(path, file)
                # res = json_file_process(
                #     os.path.join(path, file),  is_train_set)
                # yield res, path, file


def translate_html_entity(text):
    for key in HTML_ENTITY:
        if key in text:
            text = text.replace(key, HTML_ENTITY[key])
    return text


def translate_series_text_to_english(series):
    import six
    from google.cloud import translate_v2 as translate

    translate_client = translate.Client()
    result = dict()
    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    count = 0
    for data in series:
        result[data] = translate_client.translate(
            data, target_language='en')['translatedText']
        result[data] = translate_html_entity(result[data])
        count += 1
        if count % 200 == 0:
            print(count)
            print(len(result))
    return result


def df2png(df, file_name):
    fig = plt.figure(figsize=(3, 4), dpi=600)  # dpi表示清晰度
    ax = fig.add_subplot(111, frame_on=False)
    ax.xaxis.set_visible(False)  # hide the x axis
    ax.yaxis.set_visible(False)  # hide the y axis
    table(ax, df, loc='center')  # 将df换成需要保存的dataframe即可
    plt.savefig(file_name)


def generator_result():
    pass
