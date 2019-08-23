import unittest
from spacy.util import get_lang_class
from spacy.gold import GoldParse
from spacy.scorer import Scorer


class TestScorer(unittest.TestCase):

    def test_scorer(self):
        examples = [
            ('Who is Shaka Khan?', {"entities": [(7, 17, 'PERSON')]}),
            ('I like London and Berlin.', {"entities": [(7, 13, 'LOC'), (18, 24, 'LOC')]})
        ]

        lang_cls = get_lang_class("ja")
        nlp = lang_cls()

        scorer = Scorer()
        for text, _ann_ in examples:
            doc = nlp(text)
            doc_gold_text = nlp.make_doc(text)
            gold = GoldParse(doc_gold_text, entities=_ann_['entities'])
            scorer.score(doc, gold)    
        print(scorer.scores)
        raise Exception("X")
