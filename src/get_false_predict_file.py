import os
import json
from constant import PREDICT_TRUE, PREDICT, PREDICT_FALSE, NEW_LOG


if __name__ == '__main__':
    for path, __, files in os.walk():
        for file in files:
            if file.endwith('.json') and 'result' in file:
                f = open(os.path.join(path, file), 'r')
                s = json.load(f) 
    pf = open(PREDICT_FALSE, 'r')
    pf = json.load(pf)