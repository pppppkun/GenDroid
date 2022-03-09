import argparse
import json
import os

import numpy as np
import torch
from model.screen2vec.Screen2Vec import Screen2Vec
from sentence_transformers import SentenceTransformer
from model.screen2vec.prediction import TracePredictor
from model.screen2vec.autoencoder import ScreenLayout, LayoutAutoEncoder
from model.screen2vec.UI_embedding.UI2Vec import HiddenLabelPredictorModel, UI2Vec
from model.screen2vec.dataset.playstore_scraper import get_app_description
from model.screen2vec.dataset.rico_utils import get_all_labeled_uis_from_rico_screen, ScreenInfo
from model.screen2vec.dataset.rico_dao import load_rico_screen_dict

# Generates the vector embeddings for an input screen

parser = argparse.ArgumentParser()

parser.add_argument("-s", "--screen", required=True, type=str, help="path to screen to encode")
parser.add_argument("-u", "--ui_model", required=True, type=str, help="path to UI embedding model")
parser.add_argument("-n", "--num_predictors", type=int, default=4, help="number of other labels used to predict one")
parser.add_argument("-m", "--screen_model", required=True, type=str, help="path to screen embedding model")
parser.add_argument("-l", "--layout_model", required=True, type=str, help="path to layout embedding model")
parser.add_argument("-v", "--net_version", type=int, default=4,
                    help="0 for regular, 1 to embed location in UIs, 2 to use layout embedding, 3 to use both, 4 with both but no description, 5 to use both but not train description")


# args = parser.parse_args()


def get_embedding(screen, ui_model, screen_model, layout_model, num_predictors, net_version):
    if type(screen) != dict:
        with open(screen) as f:
            rico_screen = load_rico_screen_dict(json.load(f))
    else:
        rico_screen = load_rico_screen_dict(screen)
    labeled_text = get_all_labeled_uis_from_rico_screen(rico_screen)

    bert = SentenceTransformer('bert-base-nli-mean-tokens')
    bert_size = 768

    loaded_ui_model = HiddenLabelPredictorModel(bert, bert_size, 16)
    loaded_ui_model.load_state_dict(torch.load(ui_model, map_location=torch.device('cpu')), strict=False)

    ui_class = torch.tensor([UI[1] for UI in labeled_text])
    ui_text = [UI[0] for UI in labeled_text]
    UI_embeddings = loaded_ui_model.model([ui_text, ui_class])

    # avg_embedding = UI_embeddings.sum(dim=0)/len(labeled_text)

    try:
        package_name = rico_screen.activity_name.split("/")[0]
        descr = get_app_description(package_name)
    except Exception as e:
        descr = ''
        print(str(e))

    descr_emb = torch.as_tensor(bert.encode([descr]), dtype=torch.float)

    layout_autoencoder = LayoutAutoEncoder()
    layout_autoencoder.load_state_dict(torch.load(layout_model, map_location=torch.device('cpu')))
    layout_embedder = layout_autoencoder.enc
    screen_to_add = ScreenLayout(screen)
    screen_pixels = screen_to_add.pixels.flatten()
    encoded_layout = layout_embedder(torch.as_tensor(screen_pixels, dtype=torch.float).unsqueeze(0)).squeeze(0)

    if net_version in [0, 2, 6]:
        adus = 0
    else:
        # case where coordinates are part of UI rnn
        adus = 4
    if net_version in [0, 1, 6]:
        adss = 0
    else:
        # case where screen layout vec is used
        adss = 64
    if net_version in [0, 1, 2, 3]:
        desc_size = 768
    else:
        # no description in training case
        desc_size = 0

    screen_embedder = Screen2Vec(bert_size, adus, adss, net_version)
    loaded_screen_model = TracePredictor(screen_embedder, net_version)
    loaded_screen_model.load_state_dict(torch.load(screen_model, map_location=torch.device('cpu')))

    if net_version in [1, 3, 4, 5]:
        coords = torch.FloatTensor([labeled_text[x][2] for x in range(len(UI_embeddings))])
        UI_embeddings = torch.cat((UI_embeddings.cpu(), coords), dim=1)
    if net_version in [0, 1, 6]:
        screen_layout = None
    else:
        screen_layout = encoded_layout.unsqueeze(0).unsqueeze(0)

    screen_emb = screen_embedder(UI_embeddings.unsqueeze(1).unsqueeze(0), descr_emb.unsqueeze(0), None, screen_layout,
                                 False)

    if descr_emb.size()[0] == 1:
        descr_emb = descr_emb.squeeze(0)
    # baseline_emb = torch.cat((avg_embedding, descr_emb), dim=0)

    # return encoded_layout, screen_emb[0][0]
    return screen_emb[0][0]


# embeddings = get_embedding(args.screen, args.ui_model, args.screen_model, args.layout_model, args.num_predictors,
#                            args.net_version)
# print(embeddings)

def test():
    print(os.getcwd())
