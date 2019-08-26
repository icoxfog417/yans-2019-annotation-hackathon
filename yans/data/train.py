import os
import sys
import shutil
import json
import random
import time
import argparse
import spacy
from spacy.util import minibatch, compounding
from spacy.gold import GoldParse
from spacy.scorer import Scorer
import boto3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from yans.storage import Storage


def make_data(path):
    jsons = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                jsons.append(json.loads(line))
            except Exception as ex:
                print("Parse Error")
                pass

    data = []
    for j in jsons:
        d = [
            j["text"],
            {"entities": j["labels"]}
        ]
        data.append(d)

    return data


class Evaluator():

    def __init__(self, label_data):
        self.label_data = label_data
        self.golds = []

    @property
    def texts(self):
        return [t_a[0] for t_a in self.label_data]

    @classmethod
    def evaluate_from_file(cls, model_path, label_path):
        data = make_data(label_path)
        model = spacy.load(model_path)
        evaluator = cls(data)
        return evaluator.evaluate(model)

    def init_golds(self, model):
        self.get_golds(model, True)
        return self

    def get_golds(self, model, force=False):
        if len(self.golds) > 0 and not force:
            return self.golds

        self.golds = []
        for text, annotation in self.label_data:
            doc = model.tokenizer(text)
            gold = GoldParse(doc, entities=annotation["entities"])
            self.golds.append(gold)

        return self.golds

    def evaluate(self, model, force=False):
        golds = self.get_golds(model, True)
        parsed = list(model.pipe(self.texts))

        scorer = Scorer()
        for p, g in zip(parsed, golds):
            scorer.score(p, g)

        return scorer.scores


def train(annotation_path, model="ja_ginza",
          iteration=30, validation_split=0.3,
          num_limit=-1, metrics="ents_f", save_callback=None):

    spacy.prefer_gpu()
    nlp = spacy.load(model, disable=["ner"])
    nlp.tokenizer.use_sentence_separator = False

    if "JapaneseCorrector" not in nlp.pipe_names:
        corrector = nlp.create_pipe("JapaneseCorrector")
        nlp.add_pipe(corrector, last=True)

    # create new parser
    """
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner, after="parser")
    else:
        ner = nlp.get_pipe("ner")
    """
    ner = nlp.create_pipe("ner")
    nlp.add_pipe(ner, after="parser")

    data = make_data(annotation_path)

    if num_limit > 0:
        data = data[:num_limit]

    for _, annotations in data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    random.shuffle(data)
    num_test = int(len(data) * validation_split)
    train_data = data[:-num_test]
    test_data = data[-num_test:]

    best_score = -1
    train_evaluator = Evaluator(train_data).init_golds(nlp)
    test_evaluator = Evaluator(test_data).init_golds(nlp)
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()

        for itn in range(iteration):
            start = time.time()
            random.shuffle(train_data)
            losses = {}

            batches = minibatch(train_data, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(
                    texts,
                    annotations,
                    drop=0.5,
                    sgd=optimizer,
                    losses=losses,
                )

            elapse = time.time() - start
            train_score = train_evaluator.evaluate(nlp)
            score = test_evaluator.evaluate(nlp)
            print(f"{itn}: loss={losses['ner']} "
                  f"\t train_f1={train_score[metrics]:.3f}"
                  f"\t valid_f1={score[metrics]:.3f}"
                  f"\t elapse={elapse:.3f} [sec]")

            if score[metrics] > best_score and save_callback is not None:
                save_callback(nlp)
                best_score = score[metrics]

    score = test_evaluator.evaluate(nlp)
    for text, _ in test_data[:3]:
        doc = nlp(text)
        print("Entities", [(ent.text, ent.label_) for ent in doc.ents])
        print("Tokens", [(t.text, t.ent_type_, t.ent_iob) for t in doc])

    return score


def main(annotation_path, model,
         iteration, validation_split, num_limit,
         local):

    bucket = "yans.2019.js"
    auth_path = "auth/yans2019_credential.json"
    book_id = "1WDwojAFoswN_rBe0P31sKECcWeku25fgLtAG7ZSbAUo"
    storage = Storage()

    s3 = boto3.resource("s3")
    annotation_file = os.path.basename(annotation_path)

    # Get Data
    if not local:
        print(f"Get data from {annotation_path}")
        data_path = storage.path(f"raw/{annotation_file}")
        s3.Bucket(bucket).download_file(annotation_path, data_path)
        annotation_path = data_path
    else:
        print(f"Get data from {annotation_path} (local)")

    # Train Model
    print(f"Execute Training")

    def save_model(nlp):
        name, ext = os.path.splitext(annotation_file)
        _dir = storage.path(f"model/{name}")
        if os.path.exists(_dir):
            shutil.rmtree(_dir)
        os.mkdir(_dir)

        nlp.to_disk(_dir)
        shutil.make_archive(_dir, "zip", root_dir=storage.path("model"),
                            base_dir=name)
        shutil.rmtree(_dir)
        if not local:
            key = f"model/{name}.zip"
            archive = storage.path(key)
            s3.Bucket(bucket).upload_file(archive, key)

    print(f"Make Training Data")
    score = train(annotation_path, model=model,
                  iteration=iteration, validation_split=validation_split,
                  num_limit=num_limit, save_callback=save_model)

    per_label = ""
    for entity in score["ents_per_type"]:
        s = score["ents_per_type"][entity]["f"]
        per_label += f"{entity}={s} "

    # Write Result
    if not local:
        print(f"Write Result to Spread Sheet.")
        o = s3.Object(bucket, auth_path)
        j = o.get()["Body"].read().decode("utf-8")
        cred_json = json.loads(j)
        cred = ServiceAccountCredentials.from_json_keyfile_dict(
            cred_json, scopes=[
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ])
        client = gspread.authorize(cred)
        book = client.open_by_key(book_id)
        sheet = book.get_worksheet(0)
        sheet.append_row([annotation_file, score["ents_f"], per_label])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", type=str, default="data/test_teamnull.jsonl")
    parser.add_argument("--model", type=str, default="ja_ginza")
    parser.add_argument("--iteration", type=int, default=10)
    parser.add_argument("--validation_split", type=float, default=0.3)
    parser.add_argument("--num_limit", type=int, default=-1)
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    main(args.file_path,
         args.model,
         args.iteration, args.validation_split,
         args.num_limit,
         args.local)
