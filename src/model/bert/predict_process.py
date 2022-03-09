import os
import json
from utils.constant import DATA, DATA_SET, EVAL, HYBRID_TRAIN, ORIGIN_TRAIN, OLD_LOG, PREDICT_TRUE, PREDICT, \
    PREDICT_FALSE, NEW_LOG
from model.json_processor import DataSetBuild
from utils.common import files
import pandas as pd
from collections import defaultdict


def see_predict(file_path, output_path):
    predict = open(file_path, 'r')
    s = predict.read()
    l = s.split('\n')
    t = dict()
    f = dict()
    ld = dict()
    index = 0
    j = 0
    while index < len(l):
        if len(l[index]) == 0:
            index += 1
            continue
        batch = l[index:index + 4]
        text_a = batch[0][8:]
        text_b = batch[1][8:]
        label = batch[2][6:]
        prediction = batch[3][11:]
        index_ = prediction.find(' ')
        prediction = prediction[:index_] + ',' + prediction[index_:]
        prediction = eval(prediction)
        ld['text_a'] = text_a
        ld['text_b'] = text_b
        ld['label'] = label
        ld['prediction'] = prediction
        prediction = 'yes' if prediction[0] > prediction[1] else 'no'
        ld['prediction'] = prediction
        if prediction == label:
            t[j] = ld.copy()
        else:
            f[j] = ld.copy()
        j += 1
        index = index + 4
    all_data = {**t, **f}
    # all_data = f
    pre = open(output_path, 'w')
    json.dump(all_data, pre, sort_keys=True, ensure_ascii=False, indent=4)


def get_predict_false_and_file():
    pf = open(PREDICT_FALSE, 'r')
    pf = json.load(pf)
    file_predict_map = dict()
    for path in files(NEW_LOG):
        dsb = DataSetBuild(path, True)
        res = dsb.json_file_process()
        for data in res:
            # queryDoc = label.encode('utf-8')+'\t'+doc.encode('utf-8')+'\t'+ans.encode('utf-8')+'\n'
            doc = data['query']
            ans = data['positive_doc'].replace('\n', '')
            for i in pf:
                if doc in pf[i]['text_a'] or ans in pf[i]['text_b']:
                    if i not in file_predict_map:
                        file_predict_map[i] = list()
                        file_predict_map[i].append({
                            'filePath': path,
                            'info': doc + '\t' + ans
                        })
    f = open('temp.json', 'w')
    json.dump(file_predict_map, f, sort_keys=True, ensure_ascii=False, indent=4)


def get_relate_file_about_train(text_a):
    file_map = list()
    train_set = set()
    for path in files(NEW_LOG):
        dsb = DataSetBuild(path, True)
        res = dsb.json_file_process()
        for data in res:
            doc = data['query']
            ans = data['positive_doc'].replace('\n', '')
            train_set.add(doc)
            train_set.add(ans)
            if text_a in doc or '确认' in ans:
                file_map.append({
                    'filePath': path,
                    'info': doc + '\t' + ans
                })
    for path in files(OLD_LOG):
        dsb = DataSetBuild(path, False)
        res = dsb.json_file_process()
        for data in res:
            doc = data['query']
            ans = data['positive_doc'].replace('\n', '')
            train_set.add(doc)
            train_set.add(ans)
            if text_a in doc or '确认' in ans:
                file_map.append({
                    'filePath': path,
                    'info': doc + '\t' + ans
                })
    # for i in train_set:
    #     print(i)
    for i in file_map:
        print(i)


def compare_predict_files(f1, f2):
    pass


def get_all_relate_file_about_false(text_a):
    pass


def get_predict_info_from_colab_result(file_path):
    f = open(file_path, 'r')
    content = f.read().split('\n')
    result_list = []
    for i in range(len(content)):
        if content[i].startswith('text_a'):
            result_list.append([content[i], content[i + 1], content[i + 2], content[i + 3]])
    f = open(file_path, 'w')
    for i in result_list:
        f.write("\n".join(i))
        f.write('\n')
    f.close()


TP = 'TP'
TN = 'TN'
FP = 'FP'
FN = 'FN'


def compare_label_and_predict(data):
    if data['prediction'] == 'yes' and data['label'] == 'yes':
        return TP
    if data['prediction'] == 'yes' and data['label'] == 'no':
        return FP
    if data['prediction'] == 'no' and data['label'] == 'yes':
        return FN
    if data['prediction'] == 'no' and data['label'] == 'no':
        return TN


def calculate_TFPN(data_set):
    result = {
        TP: 0,
        TN: 0,
        FP: 0,
        FN: 0
    }
    for i in data_set:
        single_data = data_set[i]
        result[compare_label_and_predict(single_data)] += 1
    return result


def calculate_recall(data_set):
    res = calculate_TFPN(data_set)
    recall = res[TP] / (res[TP] + res[FN])
    return recall


def calculate_precision(data_set):
    res = calculate_TFPN(data_set)
    precision = res[TP] / (res[TP] + res[FP])
    return precision


def calculate_f1(data_set):
    recall = calculate_recall(data_set)
    precision = calculate_precision(data_set)
    f1 = 2 * recall * precision / (recall + precision)
    return f1


def show_f1_precision_and_recall(data_set):
    res = calculate_TFPN(data_set)
    for i in res:
        print(i, res[i])
    f1 = calculate_f1(data_set)
    recall = calculate_recall(data_set)
    precision = calculate_precision(data_set)
    result = 'F1:{},Precision:{},Recall:{}'.format(f1, precision, recall)
    print(result)
    # pd.DataFrame(
    #     {
    #         "recall": recall,
    #         "precision": precision,
    #         "F1": f1
    #     },
    #     index=[0]
    # ).to_latex('remove_same_data.tex')


def json_to_data_frame(json_file):
    file = json.load(open(json_file, 'r'))
    df = defaultdict(list)
    for i in file:
        i = file[i]
        df['label'].append(i['label'])
        df['prediction'].append(i['prediction'])
        df['query'].append(i['text_a'])
        df['ui_info'].append(i['text_b'])
    csv_file = json_file[:json_file.index('.')] + '.csv'
    df = pd.DataFrame(df)
    df.to_csv(csv_file, index=False)
    return pd.DataFrame(df)


def compare_predict(p1, p2):
    p1 = pd.read_csv(p1, index_col=False)
    p2 = pd.read_csv(p2, index_col=False)
    for index, item in p1.iterrows():
        item = item.to_frame().T
        if pd.merge(p2, item, on=p1.columns.to_list()).empty:
            p1.drop(index, inplace=True)
    print(p1)


if __name__ == '__main__':
    # data_set = json.load(open(os.path.join(EVAL, 'version-keep_same_data.json'), 'r'))
    # show_f1_precision_and_recall(data_set)
    data_set = json.load(open(os.path.join(EVAL, 'version-remove_same_data.json'), 'r'))
    show_f1_precision_and_recall(data_set.head())
    # p1 = os.path.join(EVAL, 'version-keep_same_data.csv')
    # p2 = os.path.join(EVAL, 'version-remove_same_data.csv')
    # compare_predict(p1, p2)
    pass
