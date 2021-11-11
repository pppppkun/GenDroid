import os
import json
from constant import INPUT, OLD_LOG, PREDICT_TRUE, PREDICT, PREDICT_FALSE, NEW_LOG
from json_processor import DataSetBuild 
from common import files

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


if __name__ == '__main__':
    get_predict_false_and_file()
    # get_relate_file_about_train(
    #     'enter the payment password again and submit the payment password and verify that the payment password is legal')
    # input = open(INPUT, 'r')
    # input = input.read()
    # s = set()
    # l = list()
    # for i in input.split('\n'):
    #     if 'enter the payment password again and submit the payment password and verify that the payment password is legal' in i:
    #         s.add(i)
    #         l.append(i)
    # print(len(s), len(l))
    # for input in s:
    #     input = input.split('\t')
    #     print(input[0], input[2])
    pass
