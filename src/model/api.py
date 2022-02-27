import json
import os
import requests
import model.tokenization as tokenization

endpoints = "http://localhost:8501/v1/models/bert:predict"
headers = {"content-type": "application-json"}
example = "This is the input string"
tokenizer = tokenization.FullTokenizer(
    vocab_file="/Users/pkun/PycharmProjects/ui_api_automated_test/output_model/1639756188/assets/vocab.txt",
    do_lower_case=True)
CLS = "[CLS]"
SEP = "[SEP]"
MAX_SEQ_LENGTH = 128


def predict_two_sentence(seq1, seq2):
    token_a = tokenizer.tokenize(seq1)
    token_b = tokenizer.tokenize(seq2)
    tokens = [CLS]
    for token in token_a:
        tokens.append(token)
    tokens.append(SEP)
    for token in token_b:
        tokens.append(token)
    segment_ids = [0] * len(tokens)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)
    input_mask = [1] * len(input_ids)

    while len(input_ids) < MAX_SEQ_LENGTH:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)

    label_id = 0
    instances = [{"input_ids": input_ids, "input_mask": input_mask, "segment_ids": segment_ids, "label_ids": label_id}]
    data = json.dumps({"signature_name": "serving_default", "instances": instances})
    response = requests.post(endpoints, data=data, headers=headers)
    prediction = json.loads(response.text)['predictions']
    # print(prediction)
    return prediction[0]


if __name__ == '__main__':
    predict_two_sentence("submit payment password authorize payment verify transaction failure",
                         "Change remaining 99998 95")
