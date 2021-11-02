import os
import json
from constant import PREDICT_TRUE, PREDICT, PREDICT_FALSE, NEW_LOG
from result_json_processor import json_file_process

# [{
#     'filePath':
#     'info':
#     'predict_info':
# }]


def files():
    for path, __, files in os.walk(NEW_LOG):
        for file in files:
            if file.endswith('.json') and 'result' in file:
                res = json_file_process(os.path.join(path, file))
                yield res, path, file


def get_predict_false_and_file():
    pf = open(PREDICT_FALSE, 'r')
    pf = json.load(pf)
    file_predict_map = dict()
    for res, path, file in files():
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


def get_all_relate_file_about_false(text_a):
    pass

if __name__ == '__main__':
    pass
