import os
import json
from constant import OLD_LOG, PREDICT_TRUE, PREDICT, PREDICT_FALSE, NEW_LOG
from result_json_processor import json_file_process

# [{
#     'filePath':
#     'info':
#     'predict_info':
# }]


def files(log, is_train_set):
    for path, __, files in os.walk(log):
        for file in files:
            if file.endswith('.json') and 'result' in file:
                res = json_file_process(
                    os.path.join(path, file),  is_train_set)
                yield res, path, file


def get_predict_false_and_file():
    pf = open(PREDICT_FALSE, 'r')
    pf = json.load(pf)
    file_predict_map = dict()
    for res, path, file in files(NEW_LOG, True):
        for data in res:
            # queryDoc = label.encode('utf-8')+'\t'+doc.encode('utf-8')+'\t'+ans.encode('utf-8')+'\n'
            doc = data['query']
            ans = data['positive_doc'].replace('\n', '')
            for i in pf:
                if doc in pf[i]['text_a'] or ans in pf[i]['text_b']:
                    if i not in file_predict_map:
                        file_predict_map[i] = list()
                        file_predict_map[i].append({
                            'filePath': os.path.join(path, file),
                            'info': doc + '\t' + ans
                        })
    f = open('temp.json', 'w')
    json.dump(file_predict_map, f, sort_keys=True, ensure_ascii=False)


def get_relate_file_about_train(text_a):
    file_map = list()
    train_set = set()
    for res, path, file in files(NEW_LOG, True):
        for data in res:
            doc = data['query']
            ans = data['positive_doc'].replace('\n', '')
            train_set.add(doc)
            train_set.add(ans)
            if text_a in doc:
                file_map.append({
                    'filePath': os.path.join(path, file),
                    'info': doc + '\t' + ans
                })
    # for i in train_set:
    #     print(i)
    for i in file_map:
        print(i)


def get_all_relate_file_about_false(text_a):
    pass


if __name__ == '__main__':
    # get_predict_false_and_file()
    get_relate_file_about_train('enter the')
