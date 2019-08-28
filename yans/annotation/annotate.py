import os
import sys
import json
import re
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from tqdm import tqdm
from yans.storage import Storage
import yans.annotation.annotators as A


def main(from_path, to_path):
    annotators = [
        A.AccountAnnotator(),
        A.CompanyAnnotator(),
        A.EvaluationAnnotator(),
        A.TimeAnnotator(),
        A.DomainAnnotator(),
        A.ProductAnnotator(),
        A.NumberAnnotator()
    ]

    annotated = []
    with open(from_path, encoding="utf-8") as f:
        lines = f.readlines()
        for d in tqdm(lines):
            instance = json.loads(d.strip())
            text = instance["text"]
            labels = []
            for a in annotators:
                _labels = a.annotate(text)
                for lb in _labels:
                    overwrap = False
                    for a_lb in labels:
                        if a_lb[0] <= lb[0] < a_lb[1] or a_lb[0] < lb[1] <= a_lb[1]:
                            overwrap = True
                            break
                    if not overwrap:
                        labels.append(lb)

            instance["labels"] = labels
            annotated.append(instance)

    with open(to_path, mode="w", encoding="utf-8") as f:
        for a in annotated:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    storage = Storage()
    _from = storage.path("interim/doccano.jsonl")
    _to = storage.path("processed/doccano_annotated.jsonl")
    main(_from, _to)
