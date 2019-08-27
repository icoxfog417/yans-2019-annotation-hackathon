import unittest
from yans.annotation.rule_annotator import RegexAnnotator
import yans.annotation.annotators as A


class TestRuleAnnotator(unittest.TestCase):

    def test_regex_annotate(self):
        annotator = RegexAnnotator()
        text = "平成26年5月にファイナンス会社のライセンス申請を行い、調査活動を継続しております"
        pattern = r"[ァ-ン]+会社"
        a = annotator.annotate(pattern, text, "XXX")
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0][0], 8)
        self.assertEqual(a[0][1], 16)
        self.assertEqual(a[0][2], "XXX")

    def test_account_annotate(self):
        annotator = A.AccountAnnotator()
        text = """
        売上高については、ＩＴ投資動向が強まりを見せる分野において顧客ニーズを的確に捉えたこと等が牽引し、
前年同期を上回りました。営業利益については、増収効果や収益性向上（売上総利益率は前年同期比2.2ポイント
増の22.2％に向上）による売上総利益の増加が構造転換に向けた対応強化による費用を中心とする販売費及び一
般管理費の増加を吸収したことから前年同期比増益となり、営業利益率は8.0％（前年同期比2.0ポイント増）と
なりました。経常利益及び親会社株主に帰属する四半期純利益については、主に営業利益の増加を背景として前
年同期比増益となりました。 
        """

        a = annotator.annotate(text)
        """
        営業利益率
        販売費
        営業利益
        売上高
        売上総利益率
        経常利益
        売上総利益
        """
        self.assertEqual(len(a), 7)

    def test_company_annptator(self):
        annotator = A.CompanyAnnotator()
        text = "ほげほげ山太郎株式会社の売上は、株式会社エックスよりも低かった"
        a = annotator.annotate(text)
        self.assertEqual(len(a), 2)
        self.assertEqual(text[a[0][0]:a[0][1]], "山太郎株式会社")
        self.assertEqual(text[a[1][0]:a[1][1]], "株式会社エックス")

    def test_evaluation_annptator(self):
        annotator = A.EvaluationAnnotator()
        text = """
        売上高については、ＩＴ投資動向が強まりを見せる分野において顧客ニーズを的確に捉えたこと等が牽引し、
前年同期を上回りました。営業利益については、増収効果や収益性向上（売上総利益率は前年同期比2.2ポイント
増の22.2％に向上）による売上総利益の増加が構造転換に向けた対応強化による費用を中心とする販売費及び一
般管理費の増加を吸収したことから前年同期比増益となり、営業利益率は8.0％（前年同期比2.0ポイント増）と
なりました。経常利益及び親会社株主に帰属する四半期純利益については、主に営業利益の増加を背景として前
年同期比増益となりました。 
        """.replace("\n", "")

        a = annotator.annotate(text)
        annotator.show_entity(text, a)
        self.assertEqual(len(a), 11)

    def test_number_annptator(self):
        annotator = A.NumberAnnotator()
        text = """
        売上高については、ＩＴ投資動向が強まりを見せる分野において顧客ニーズを的確に捉えたこと等が牽引し、
前年同期を上回りました。営業利益については、増収効果や収益性向上（売上総利益率は前年同期比122.21ポイント
増の22.2％に向上）による売上総利益の増加が構造転換に向けた対応強化による費用を中心とする販売費及び一
般管理費の増加を吸収したことから前年同期比増益となり、営業利益率は8.0％（前年同期比2.0ポイント増）と
なりました。経常利益及び親会社株主に帰属する四半期純利益については、主に営業利益の増加を背景として五十五億円となりました。 
        """.replace("\n", "")

        a = annotator.annotate(text)
        annotator.show_entity(text, a)
        self.assertEqual(len(a), 5)

    def test_product_annptator(self):
        annotator = A.ProductAnnotator()
        text = "わが社では、「ハイ・エンド・エーアイ」と『ワンピース』の売り上げが好調でした。"
        a = annotator.annotate(text)
        annotator.show_entity(text, a)
        self.assertEqual(len(a), 2)

    def test_time_annptator(self):
        annotator = A.TimeAnnotator()
        text = "当会計年度の平成28年7月から無担保カードローンの下限利率を4.7%から3.0%に改定いたしました上半期に。"
        a = annotator.annotate(text)
        annotator.show_entity(text, a)
        self.assertEqual(len(a), 4)

    def test_dom_annptator(self):
        annotator = A.DomainAnnotator()
        text = """
その他の事業につきましては、医療介護連携事業において、政府が進める「地域包括ケアシステム」
構築を支援するツールとしてクリニック向け・薬局向け・介護サービス事業者向けに提供する
「ひろがるケアネット」を3月にリリース
        """.replace("\n", "")

        a = annotator.annotate(text)
        annotator.show_entity(text, a)
        self.assertEqual(len(a), 2)
