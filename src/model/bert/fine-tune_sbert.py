import os

from sentence_transformers import SentenceTransformer, InputExample, losses, util
from torch.utils.data import DataLoader
from collections import namedtuple
import csv


def get_train_set_from_csv(file_path):
    train_set = []
    with open(file_path) as f:
        f_csv = csv.reader(f)
        headings = next(f_csv)
        Row = namedtuple('Row', headings)
        data_item = namedtuple('data_item', ['texts', 'label'])
        for r in f_csv:
            row = Row(*r)
            d = data_item(texts=[row.sentence1, row.sentence2], label=float(row.score))
            train_set.append(d)
            # Process row
    return train_set

def fine_tune(train_set):
    # Define the model. Either from scratch of by loading a pre-trained model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # model = SentenceTransformer('./output_model')
    train_examples = list(
        map(
            lambda data_item: InputExample(texts=data_item.texts, label=data_item.label),
            train_set
        )
    )

    # Define your train examples. You need more than just two examples...
    # train_examples = [InputExample(texts=['fill task name', 'resource id is new task name'], label=0.8),
    #                   InputExample(texts=['fill task name', 'text is name'], label=0.8),
    #                   InputExample(
    #                       texts=['fill task description', 'resource id is new task description'],
    #                       label=0.8),
    #                   InputExample(
    #                       texts=['fill task description', 'text is description'],
    #                       label=0.8),
    #                   InputExample(texts=['fill task name', 'text is description'], label=0.2),
    #                   InputExample(texts=['fill task name', 'resource id is new task description'], label=0.2),
    #                   InputExample(texts=['fill task description', 'text is name'], label=0.2),
    #                   InputExample(texts=['fill task description', 'resource id is new task name'], label=0.2),
    #                   InputExample(texts=['fill task information', 'name and description'], label=0.9)]

    # Define your train dataset, the dataloader and the train loss
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
    train_loss = losses.CosineSimilarityLoss(model)
    os.system('rm -r ./output_model')
    # Tune the model
    model.fit(train_objectives=[(train_dataloader, train_loss)], epochs=20, warmup_steps=100,
              output_path='./output_model')


def predict():
    model = SentenceTransformer('./output_model/')
    emd1 = model.encode('select all mail')
    # emd2 = model.encode(['site settings', 'settings'])
    emd2 = model.encode('Double tap to select this conversation')
    a = sorted(util.cos_sim(emd1, emd2)[0], key=lambda x: -x)
    print(a)


if __name__ == '__main__':
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # emd1 = model.encode('More option')
    # emd2 = model.encode('more icon')
    # print(util.cos_sim(emd1, emd2))
    # train_set = get_train_set_from_csv('data.csv')
    # fine_tune(train_set)
    predict()
