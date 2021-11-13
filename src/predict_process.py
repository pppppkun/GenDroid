import os
import json
from constant import INPUT, OLD_LOG, PREDICT_TRUE, PREDICT, PREDICT_FALSE, NEW_LOG
from json_processor import DataSetBuild 
from common import files

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
        batch = l[index:index+4]
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
        if prediction == label:
            t[j] = ld.copy()
        else:
            f[j] = ld.copy()
        j += 1
        index = index + 4 
    # all_data = {**t, **f} 
    all_data = f
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
                    'filePath':  path,
                    'info': doc + '\t' + ans
                })
    # for i in train_set:
    #     print(i)
    for i in file_map:
        print(i)


def get_all_relate_file_about_false(text_a):
    pass


def get_predict_info_from_file(file_path):
    f = open(file_path,'r')
    content = f.read().split('\n')
    result_list = []
    for i in range(len(content)):
        if content[i].startswith('text_a'):
            result_list.append([content[i],content[i+1],content[i+2],content[i+3]])
    f = open(file_path, 'w')
    for i in result_list:
        f.write("\n".join(i))
        f.write('\n')
    f.close()
if __name__ == '__main__':
    # get_predict_info_from_file('data/hybrid-predict.txt')
    see_predict(os.path.join('data', 'hybrid-predict.txt'), os.path.join('data', 'hybrid-false-predict.json'))
    pass