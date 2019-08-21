# yans-2019-annotation-competition

Yans2019 Annotation Competition

## Train NER model

1. Download data: `python yans/data/prepare.py`
2. Upload data to doccano: (upload `data/interim/doccano.jsonl`)
3. Annotation on doccano!
4. Download annotated data to `data/raw/annotation.jsonl`
5. Train spaCy NER model: `python yans/data/train.py`


## (Japanese NER Training Preparation)

Train Japanese model following [Add ja_core_web_md-2.1.0](https://github.com/explosion/spacy-models/pull/16).

```py
python yans/data/ner_train_ja_example.py
```
