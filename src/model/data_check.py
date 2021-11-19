import json
import os
from constant import DATA, NEW_LOG, OLD_LOG, ORIGIN_TRAIN, VERSION_TRAIN, HTML_ENTIRY
from common import files




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


def origin_data_set_to_dict(origin_data_set):
    result = dict()
    for i in origin_data_set:
        if len(i) == 0:
            continue
        single_data = i.split('\t')
        label_and_text = result.setdefault(single_data[1], [])
        label_and_text.append({'label':single_data[0], 'text':single_data[2]})
    return result

def get_all_text_b(dict_data_set):
    result = dict()
    for key in dict_data_set.keys():
        s = result.setdefault(key, set())
        for i in dict_data_set[key]:
            s.add(i['label'] + ' ' + i['text'])
    return result 

def compare_data_set(f1, f2):
    f1_strs = open(f1, 'r').read().split('\n')
    f2_strs = open(f2, 'r').read().split('\n')
    dict1 = origin_data_set_to_dict(f1_strs) 
    f1_text_a_and_text_b_dict = get_all_text_b(dict1)
    dict2 = origin_data_set_to_dict(f2_strs)
    f2_text_a_and_text_b_dict = get_all_text_b(dict2)
    result = dict()
    f1_keys = set(f1_text_a_and_text_b_dict.keys())
    f2_keys = set(f2_text_a_and_text_b_dict.keys())
    same_keys = f1_keys.intersection(f2_keys)
    for i in same_keys:
        l1 = set(f1_text_a_and_text_b_dict[i])
        l2 = set(f2_text_a_and_text_b_dict[i])
        result[i] = {
            'only_' + f2: l2.difference(l1),
            'only_' + f1: l1.difference(l2)
            # 'same': l1.intersection(l2)
        }
    for i in f1_keys.difference(f2_keys):
        result[i] = {
            'only_' + f1: f1_text_a_and_text_b_dict[i]
        }
    for i in f2_keys.difference(f1_keys):
        result[i] = {
            'only_' + f2: f2_text_a_and_text_b_dict[i]
        }
    for i in result:
        for j in result[i]:
            result[i][j] = sorted(list(result[i][j]))
    json.dump(result, open('temp.json', 'w'), ensure_ascii=False, indent=4, sort_keys=True)

def translate_html_to_ascii(data_set_path):
    data_set = open(data_set_path, 'r').read().split('\n')
    result = []
    for i in data_set:
        temp = i
        for key in HTML_ENTIRY:
            if key in temp:
                temp = temp.replace(key, HTML_ENTIRY[key])
        result.append(temp)
    f = open('change_data_set.txt', 'w')
    f.write('\n'.join(result))


if __name__ == '__main__':
    # compare_from_trace()
    # check_false()
    translate_html_to_ascii('data/data_set/version_data_set.tsv')
    # compare_data_set('change_data_set.txt', 'data/data_set/origin_data_set.tsv')
