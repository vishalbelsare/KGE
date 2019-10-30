import os
import interact
from train import model_fn
from pathlib import Path
import functools
import json
import pickle

import tensorflow as tf
import pprint
pp = pprint.PrettyPrinter(indent=2)

pickle_path = './SFM_STARTER'
DATADIR = 'SFM_STARTER'
PARAMS = './results/params.json'
MODELDIR = './results/model'

# Predict
with Path(PARAMS).open() as f:
    params = json.load(f)
params['words'] = str(Path(DATADIR, 'vocab.words.txt'))
params['chars'] = str(Path(DATADIR, 'vocab.chars.txt'))
params['tags'] = str(Path(DATADIR, 'vocab.tags.txt'))
params['glove'] = str(Path(DATADIR, 'glove.npz'))
estimator = tf.estimator.Estimator(model_fn, MODELDIR, params=params)

def get_prediction(line):
    predict_inpf = functools.partial(interact.predict_input_fn, line)
    for pred in estimator.predict(predict_inpf):
        pred_tags = pred['tags']
        break
    return pred_tags

def correct_token_position(sentence, query_idx, word):
    for offset in range(10):
        left_idx = query_idx - offset
        if sentence[left_idx: left_idx + len(word)] == word:
            return (left_idx, left_idx + len(word))
        right_idx = query_idx + offset
        if sentence[right_idx: right_idx + len(word)] == word:
            return (right_idx, right_idx + len(word))
    return None


if __name__ == '__main__':
    with open(os.path.join(pickle_path, "dataset_sentences.pickle"),"rb") as pickle_file:
        dataset_sentences = pickle.load(pickle_file)
    with open(os.path.join(pickle_path, "dataset_labels.pickle"),"rb") as pickle_file:
        dataset_labels = pickle.load(pickle_file)
    # pp.pprint(dataset_labels)
    # pp.pprint(dataset_sentences)

    sentence_pred_tags = {}
    test_count = 1
    for sentence in dataset_sentences.keys():
        if sentence not in sentence_pred_tags:
            sentence_pred_tags[sentence] = {}

        pred_tags = get_prediction(sentence)
        cur_idx = 0
        entity_start = 0
        entity_end = 0
        prev_tag = None
        words = sentence.strip().split()
        for i in range(len(words)):
            word = words[i]
            tag = pred_tags[i].decode()

            if tag[0] != 'O':
                corrected_start, corrected_end = correct_token_position(sentence, cur_idx, word)
                if tag[0] == 'B' or \
                    (prev_tag is not None and prev_tag == 'O'):
                    entity_start = corrected_start
                entity_end = corrected_end
                if i + 1 >= len(words) or pred_tags[i + 1].decode()[0] != 'I':
                    sentence_pred_tags[sentence][(entity_start, entity_end)] = tag[2:]

            cur_idx += len(word) + 1
            prev_tag = tag
        test_count += 1

    with open("sentence_pred_tags.pickle","wb") as pickle_out:
        pickle.dump(sentence_pred_tags, pickle_out)