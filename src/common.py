import os

def files(log):
    for path, __, files in os.walk(log):
        for file in files:
            if file.endswith('.json') and 'result' in file:
                yield os.path.join(path, file) 
                # res = json_file_process(
                #     os.path.join(path, file),  is_train_set)
                # yield res, path, file