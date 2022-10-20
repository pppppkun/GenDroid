import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import precision_recall_fscore_support
from joblib import dump, load

model = load('rf.joblib')


def process_data():
    origin_data = pd.read_csv('/Users/pkun/PycharmProjects/ui_api_automated_test/decision_data/origin_data.csv')
    data = origin_data.iloc[:, :-1]
    label = origin_data.iloc[:, -1]
    return data.values, label


def train():
    data, label = process_data()
    Xtrain, Xtest, Ytrain, Ytest = train_test_split(data, label, test_size=0.3, random_state=100)
    # search hyper param
    n_estimators = [int(x) for x in np.linspace(start=0, stop=200)]
    max_features = ['log2', 'sqrt', None]
    max_depth = [int(x) for x in np.linspace(1, 110)]
    max_depth.append(None)
    min_samples_split = [2, 5, 10]
    min_samples_leaf = [1, 2, 4]
    bootstrap = [True, False]
    random_grid = {'n_estimators': n_estimators,
                   'max_features': max_features,
                   'max_depth': max_depth,
                   'min_samples_split': min_samples_split,
                   'min_samples_leaf': min_samples_leaf,
                   'bootstrap': bootstrap}
    # rf = RandomForestClassifier()
    # rf_random = RandomizedSearchCV(estimator=rf, param_distributions=random_grid, n_iter=1000, cv=10, verbose=2,
    #                                random_state=42, n_jobs=-1)
    # print(rf_random.best_params_)
    # print(rf_random.score(Xtest, Ytest))
    rf = RandomForestClassifier(
        **{'n_estimators': 106, 'min_samples_split': 5, 'min_samples_leaf': 4, 'max_features': 'sqrt', 'max_depth': 38,
           'bootstrap': True}, random_state=100)
    rf.fit(Xtrain, Ytrain)
    print(rf.score(Xtest, Ytest))
    predict = rf.predict(data)
    print(predict)
    print(precision_recall_fscore_support(label, predict, labels=[1]))
    dump(rf, 'rf.joblib')


def predict(x):
    return model.predict(x)