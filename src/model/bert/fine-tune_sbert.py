from sentence_transformers import SentenceTransformer, InputExample, losses, util
from torch.utils.data import DataLoader


def fine_tune():
    # Define the model. Either from scratch of by loading a pre-trained model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Define your train examples. You need more than just two examples...
    train_examples = [InputExample(texts=['fill task name', 'resource id is new task name'], label=0.8),
                      InputExample(texts=['fill task name', 'text is name'], label=0.8),
                      InputExample(
                          texts=['fill task description', 'resource id is new task description'],
                          label=0.8),
                      InputExample(
                          texts=['fill task description', 'text is description'],
                          label=0.8),
                      InputExample(texts=['fill task name', 'text is description'], label=0.2),
                      InputExample(texts=['fill task name', 'resource id is new task description'], label=0.2),
                      InputExample(texts=['fill task description', 'text is name'], label=0.2),
                      InputExample(texts=['fill task description', 'resource id is new task name'], label=0.2),
                      InputExample(texts=['fill task information', 'name and description'], label=0.9)]

    # Define your train dataset, the dataloader and the train loss
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
    train_loss = losses.CosineSimilarityLoss(model)

    # Tune the model
    model.fit(train_objectives=[(train_dataloader, train_loss)], epochs=20, warmup_steps=100,
              output_path='./output_model')


def predict():
    model = SentenceTransformer('./output_model/')
    emd1 = model.encode('fill task information')
    emd2 = model.encode(['name and description', 'name', 'description'])
    print(util.cos_sim(emd1, emd2))


if __name__ == '__main__':
    fine_tune()
    predict()
