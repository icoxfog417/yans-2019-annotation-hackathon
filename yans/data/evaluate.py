import os
import sys
import json
from zipfile import ZipFile
import argparse
import boto3
import spacy
import pprint
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from yans.storage import Storage
from yans.data.train import Evaluator, make_data


def main(model_path, data_path,
         num_limit, local):

    bucket = "yans.2019.js"
    storage = Storage()

    # Load model
    s3 = boto3.resource("s3")
    print(f"Load model from {model_path}")
    if not local:
        _model_path = storage.path(f"model/{os.path.basename(model_path)}")
        if not os.path.exists(_model_path):
            s3.Bucket(bucket).download_file(model_path, _model_path)
    else:
        _model_path = storage.path(model_path)

    expand_path, _ = os.path.splitext(_model_path)
    if not os.path.exists(expand_path):
        with ZipFile(_model_path) as f:
            f.extractall(storage.path("model"))

    nlp = spacy.load(expand_path)

    # Load Data
    print(f"Get data from {data_path}")
    _data_path = data_path
    if not local:
        _data_path = storage.path(f"raw/{os.path.basename(data_path)}")
        if not os.path.exists(_data_path):
            s3.Bucket(bucket).download_file(data_path, _data_path)

    # Evaluate
    print("Evaluator model")
    data = make_data(_data_path)
    if num_limit > 0:
        data = data[:num_limit]
    evaluator = Evaluator(data)
    score = evaluator.evaluate(nlp)
    pprint.pprint(score)

    file_name = f"{os.path.basename(model_path)}_{os.path.basename(data_path)}.json"
    with open(file_name, mode="w", encoding="utf-8") as f:
        json.dump(score, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str)
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--num_limit", type=int, default=-1)
    parser.add_argument("--local", action="store_true")
    args = parser.parse_args()

    main(args.model_path,
         args.data_path,
         args.num_limit,
         args.local)
