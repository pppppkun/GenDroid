import os

DATA_INDEX = {
    'label',
    'query',
    'ui_info',
    'prediction'
}

DATA = 'data'
DATA_SET = os.path.join(DATA, 'data_set')
EVAL = os.path.join(DATA, 'eval')

ORIGIN_TRAIN = os.path.join(DATA_SET ,'origin_train.tsv')
ORIGIN_TEST = os.path.join(DATA_SET, 'origin_test.tsv')
HYBRID_TRAIN = os.path.join(DATA_SET, 'hybrid_train.tsv')
HYBRID_TEST = os.path.join(DATA_SET, 'hybrid_test.tsv')
VERSION_TRAIN = os.path.join(DATA_SET, 'version_train.tsv')
VERSION_TEST = os.path.join(DATA_SET, 'version_test.tsv')
NEW_VERSION_DATA = os.path.join(DATA_SET, 'new_version_data_set.tsv')
OLD_VERSION_DATA = os.path.join(DATA_SET, 'old_version_data_set.tsv')
PREDICT_FALSE = os.path.join(DATA, 'predict_false.json')
PREDICT_TRUE = os.path.join(DATA, 'predict_true.json')
PREDICT = os.path.join(DATA, 'predict.json')
NEW_LOG = os.path.join(DATA, 'new_test_log') 
OLD_LOG = os.path.join(DATA, 'old_test_log')

HTML_ENTIRY = {
    '&quot;': '\"',
    '&#39;':'\''
}

