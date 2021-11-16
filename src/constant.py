import os

DATA = 'data'
DATA_SET = os.path.join(DATA, 'data_set')

ORIGIN_INPUT = os.path.join(DATA_SET ,'origin_input.tsv')
ORIGIN_OUTPUT = os.path.join(DATA_SET, 'origin_output.tsv')
HYBRID_INPUT = os.path.join(DATA_SET, 'hybrid_input.tsv')
HYBRID_OUTPUT = os.path.join(DATA_SET, 'hybrid_output.tsv')
VERSION_INPUT = os.path.join(DATA_SET, 'version_input.tsv')
VERSION_OUTPUT = os.path.join(DATA_SET, 'version_output.tsv')

PREDICT_FALSE = os.path.join(DATA, 'predict_false.json')
PREDICT_TRUE = os.path.join(DATA, 'predict_true.json')
PREDICT = os.path.join(DATA, 'predict.json')
NEW_LOG = os.path.join(DATA, 'new_test_log') 
OLD_LOG = os.path.join(DATA, 'old_test_log')