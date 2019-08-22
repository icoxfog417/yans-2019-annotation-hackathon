import json
import boto3


def main():
    bucket = "yans.2019.js"
    target = "auth/credentials.json"

    s3 = boto3.resource("s3")
    o = s3.Object(bucket, target)
    j = o.get()["Body"].read().decode("utf-8")
    cred = json.loads(f)

    



if __name__ == "__main__":
    main()
