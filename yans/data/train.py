import os
import sys
import json
import random
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from tqdm import tqdm
from wasabi import Printer
import spacy
from spacy.util import get_lang_class, minibatch, compounding
import spacy.cli.train as train_util
from yans.storage import Storage


def make_data(storage, path, validation_split=0.3):
    jsons = []
    with open(storage.path(path), encoding="utf-8") as f:
        jsons = [json.loads(line) for line in f.readlines()]

    data = []
    for j in jsons:
        d = [
            j["text"],
            {"entities": j["labels"]}
        ]
        data.append(d)

    return data


def train(data, vectors="", odel="ja", validation_split=0.3, iteration=30,
          output_path="model/trained"):
    lang_cls = get_lang_class("ja")
    nlp = lang_cls()
    msg = Printer()

    if vectors:
        train_util._load_vectors(nlp, vectors)

    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner, last=True)
    else:
        ner = nlp.get_pipe("ner")

    for _, annotations in data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    random.shuffle(data)
    num_test = int(len(data) * validation_split)
    train_data = data[:-num_test]
    test_data = data[-num_test:]

    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]

    optimizer = nlp.begin_training()
    with nlp.disable_pipes(*other_pipes):
        for itn in range(iteration):
            random.shuffle(train_data)
            losses = {}

            batches = minibatch(data, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(
                    texts,
                    annotations,
                    drop=0.5,
                    sgd=optimizer,
                    losses=losses,
                )
            print(losses)

    storage = Storage()
    _dir = storage.path(output_path)
    if not os.path.exists(_dir):
        os.mkdir(_dir)

    nlp.to_disk(_dir)
    print("Saved model to", _dir)

    # test the saved model
    print("Loading from", _dir)
    nlp2 = spacy.load(_dir)
    for text, _ in test_data[:3]:
        doc = nlp2(text)
        print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
        print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])


def main(annotation_file, validation_split=0.3):
    storage = Storage()
    data = make_data(storage, f"raw/{annotation_file}", validation_split)
    train(data)


if __name__ == "__main__":
    main("annotation.jsonl")
