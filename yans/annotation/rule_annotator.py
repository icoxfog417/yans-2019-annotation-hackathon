import re


class RegexAnnotator():

    def __init__(self):
        pass

    def annotate(self, pattern, text, tag):
        annotation = []
        for c in re.finditer(pattern, text):
            a = list(c.span()) + [tag]
            annotation.append(a)
        return annotation

    @classmethod
    def show_entity(cls, text, annotations):
        for a in annotations:
            print(text[a[0]:a[1]])
