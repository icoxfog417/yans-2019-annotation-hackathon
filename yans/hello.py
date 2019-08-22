import json
import boto3
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def main():
    bucket = "yans.2019.js"
    target = "auth/yans2019_credential.json"

    s3 = boto3.resource("s3")
    o = s3.Object(bucket, target)
    j = o.get()["Body"].read().decode("utf-8")
    cred_json = json.loads(j)

    cred = ServiceAccountCredentials.from_json_keyfile_dict(
            cred_json, scopes=[
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ])

    client = gspread.authorize(cred)
    book_id = "1WDwojAFoswN_rBe0P31sKECcWeku25fgLtAG7ZSbAUo"
    book = client.open_by_key(book_id)
    sheet = book.get_worksheet(0)
    sheet.append_row([0, "Hello!"])


if __name__ == "__main__":
    main()
