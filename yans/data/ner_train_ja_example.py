import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from spacy.cli.train import train
from yans.storage import Storage


def main():
    storage = Storage()

    # Download pretrained vector
    url = "https://github.com/megagonlabs/UD_Japanese-PUD/releases/download/ja_pud-2.1.0/ja_pud-2.1.0.tar.gz"
    vector_path = storage.path("vector/ja_pud-2.1.0")

    if not os.path.exists(vector_path):
        tar = storage.download(url, directory="vector")
        vector_path = storage.extractall(tar)

    # Download example data
    url = "https://raw.githubusercontent.com/megagonlabs/UD_Japanese-PUD/v2.4-NE-spacy/ja_pud-ud-test.test.json"
    train_path = storage.download(url, directory="processed")

    url = "https://raw.githubusercontent.com/megagonlabs/UD_Japanese-PUD/v2.4-NE-spacy/ja_pud-ud-test.train.json"
    test_path = storage.download(url, directory="processed")

    # Train NER by spaCy
    output_path = storage.path("model/example_model")
    train("ja", output_path, train_path, test_path,
          pipeline="tagger,parser,ner",
          vectors=vector_path,
          parser_multitasks="dep,tag",
          entity_multitasks="dep,tag",
          n_early_stopping=5,
          verbose=True)


if __name__ == "__main__":
    main()
