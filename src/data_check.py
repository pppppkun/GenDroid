import json
import os
from constant import DATA, NEW_LOG, OLD_LOG
from common import files
def see_predict():
    predict = open(os.path.join('data','predict.txt'), 'r')
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
        if prediction == label:
            t[j] = ld.copy()
        else:
            f[j] = ld.copy()
        j += 1
        index = index + 5
    all_data = {**t, **f} 
    pre = open('data/predict1.json', 'w')
    json.dump(all_data, pre, sort_keys=True, ensure_ascii=False, indent=4)


def get_trace(log):
    traces = {}
    index = 2 if log == NEW_LOG else 1 
    process_trace = lambda trace_list : [ call[: call.index('line')].strip(' ')  for call in trace_list[0: len(trace_list)-index]]
    for path in files(log):
        f = open(path, 'r')
        f = json.load(f) 
        case_data = f['case_data'] 
        trace = list()
        for case in case_data:
            if 'trace' in case:
                _ = process_trace(case['trace'].split('\n'))
                _.reverse()
                trace.append(_)  
        if len(trace) != 0:
            traces[path] = trace
    return traces

def trace2file(log_path, file):
    new_trace = get_trace(log_path) 
    # old_trace = get_trace(OLD_LOG)
    trace_file = open(os.path.join(DATA, file), 'w')
    for i in new_trace:
        trace = new_trace[i]  
        trace_file.write(i+'\n')  
        for j in trace:
            trace_file.write('\t')
            trace_file.write(j.__str__()+'\n')

# return the intersection of two log
def compare_from_trace():
    new_trace = get_trace(NEW_LOG) 
    old_trace = get_trace(OLD_LOG)
    # api_index = 0 if log == OLD_LOG else 3
    new_trace_set = set()
    old_trace_set = set() 
    get_trace_from_traces = lambda traces, y : set( j[y] for i in traces for j in traces[i])
    new_trace_set = get_trace_from_traces(new_trace, 3)
    old_trace_set = get_trace_from_traces(old_trace, 0)
    join_set = new_trace_set.intersection(old_trace_set) 
    join_set.remove('system_requests_from_direct_business')
    file_index = dict()
    for i in new_trace:
        for j in new_trace[i]:
            for trace in j:
                if trace in join_set:
                    l = file_index.setdefault(trace, set())
                    l.add(i)
    for trace in file_index:
        copy_set = file_index[trace].copy()
        for file in copy_set:
            j = json.load(open(file, 'r'))
            if j['success']:
                file_index[trace].remove(file) 

# find the relation between assert_list and case_data and success
def check_false():
    old_result = json.load(open('data/old_test_log/36591/1614758900_result_test_1receipts_214333.json', 'r')) 
    new_result = json.load(open('data/new_test_log/2490/1620974239_result_test_1Receipts_323680.json', 'r'))
    case_doc = new_result['case_doc'] 
    print(new_result.keys())
    print(case_doc)
    print(new_result['success'])
    print(new_result['errors'])
     
if __name__ == '__main__':
    # compare_from_trace()
    check_false()