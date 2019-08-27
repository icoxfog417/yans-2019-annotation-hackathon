import os
import re
import spacy
from yans.annotation.rule_annotator import RegexAnnotator


class AccountAnnotator():

    def __init__(self):
        self._accounts = set()
        # https://www.fsa.go.jp/search/20190228.html
        path = os.path.join(os.path.dirname(__file__), "accounts.csv")
        with open(path, encoding="utf-8") as f:
            accounts = f.readlines()
            for a in accounts:
                a_normalize = a.strip().replace("（△）", "").split("又は")
                for _a in a_normalize:
                    if _a:
                        self._accounts.add(_a)
                        if _a.endswith("利益"):
                            self._accounts.add(_a + "率")

    def annotate(self, text):
        annotations = []
        for a in self._accounts:
            if a in text:
                start = text.index(a)
                end = start + len(a)
                annotations.append([
                    start, end, "ACT"
                ])

        return annotations


class CompanyAnnotator(RegexAnnotator):

    def annotate(self, text):
        pattern = r"(株式会社[ァ-ン一-龥・]+)|([ァ-ン一-龥・]+会社)"
        annotations = super().annotate(pattern, text, "CMP")
        return annotations


class EvaluationAnnotator(RegexAnnotator):

    def __init__(self):
        self._model = spacy.load("ja_ginza")

    def annotate(self, text):
        parsed = self._model(text)

        annotations = []
        eval_dict = ["増", "減", "上回", "下回", "向上", "下降"]
        preserve = []
        head = []
        for t in parsed:
            if t.pos_ in ["NOUN", "VERB"]:
                for e in eval_dict:
                    if e in t.text:
                        head = preserve + [t]
                        break

                if len(head) == 0 and t.pos_ == "NOUN" and re.match("[一-龥]+", t.text):
                    preserve.append(t)
                else:
                    preserve.clear()

            elif len(head) > 0 and t.pos_ == "AUX":
                head.append(t)
            elif len(head) > 0 and t.pos_ == "NOUN":
                head.append(t)
            else:
                if len(head) > 0:
                    start = head[0].idx
                    length = sum([len(n.text) for n in head])
                    annotations.append([start, start + length, "EVL"])
                    head.clear()
                preserve.clear()

        return annotations


class NumberAnnotator(RegexAnnotator):

    def annotate(self, text):
        pattern = r"[0-9〇一二三四五六七八九十百千万億兆\.,]{2,}(円|%|％)?"
        annotations = super().annotate(pattern, text, "NUM")
        return annotations


class ProductAnnotator(RegexAnnotator):

    def annotate(self, text):
        pattern = r"(「|『).+?(」|』)"
        annotations = super().annotate(pattern, text, "PRD")
        for a in annotations:
            a[0] = a[0] + 1
            a[1] = a[1] - 1

        return annotations


class TimeAnnotator(RegexAnnotator):

    def annotate(self, text):
        pattern = r"[平成昭和令和当前連結会計四半上中下旬0-9]+(年度|年|期|月|日)"
        annotations = super().annotate(pattern, text, "TIME")
        return annotations


class DomainAnnotator(RegexAnnotator):

    def __init__(self):
        self._model = spacy.load("ja_ginza")

    def annotate(self, text):
        parsed = self._model(text)

        preserved = []
        annotations = []
        for t in parsed:
            if t.pos_ == "NOUN":
                preserved.append(t)
                if "事業" in t.text or "部門" in t.text or "事業部門" in t.text:
                    if len(preserved) == 1:
                        continue
                    start = preserved[0].idx
                    length = sum([len(n.text) for n in preserved])
                    annotations.append([start, start + length, "DOM"])
                    preserved.clear()
            else:
                preserved.clear()

        return annotations
