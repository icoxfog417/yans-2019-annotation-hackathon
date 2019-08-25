import os
import sys
import json
import unicodedata
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from tqdm import tqdm
from yans.storage import Storage


def chabsa_to_doccano(directory):
    storage = Storage()
    doccano_file = storage.path("interim/doccano.jsonl")
    doccano_filep = open(doccano_file, mode="w", encoding="utf-8")

    def normalize(text):
        _text = text
        _text = unicodedata.normalize("NFKC", _text).strip()
        return _text

    for f in tqdm(os.listdir(directory)):
        path = os.path.join(directory, f)
        if not os.path.isfile(path) or not f.endswith(".json"):
            continue

        chabsa = {}
        with open(path, encoding="utf-8") as cf:
            chabsa = json.load(cf)

        for s in chabsa["sentences"]:
            doccano = {}
            doccano["text"] = normalize(s["sentence"])
            doccano["labels"] = []
            doccano["meta"] = {}
            for k in chabsa["header"]:
                doccano["meta"][k] = chabsa["header"][k]
                doccano["meta"]["sentence_id"] = s["sentence_id"]
            doccano_filep.write(json.dumps(doccano, ensure_ascii=False) + "\n")

    doccano_filep.close()
    return doccano_file


def main():
    storage = Storage()

    # Download chABSA-dataset
    url = "https://s3-ap-northeast-1.amazonaws.com/dev.tech-sketch.jp/chakki/public/chABSA-dataset.zip"
    zip = storage.download(url, directory="raw")
    data_dir = storage.extractall(zip)
    chabsa_to_doccano(data_dir)


if __name__ == "__main__":
    main()
