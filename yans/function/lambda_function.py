import os
import json
import urllib.request
import boto3


def lambda_handler(event, context):
    s3 = boto3.resource("s3")
    ecs = boto3.client("ecs")
    bucket = "yans.2019.js"
    slack_token = os.getenv("SLACK_TOKEN")
    iteration = os.getenv("ITERATION")

    uploaded = []
    for r in event["Records"]:
        key = r["s3"]["object"]["key"]
        print(f"Get {key}")
        obj = s3.Object(bucket, key)
        file_url = obj.get()["Body"].read().decode("utf-8").strip()

        file_name = os.path.basename(key)
        file_root, ext = os.path.splitext(file_name)
        _, ext = os.path.splitext(file_url)

        if ext not in [".json", ".jsonl"]:
            continue

        print(f"Download {file_url}")
        request = urllib.request.Request(file_url, headers={
            "Authorization": f"Bearer {slack_token}"
        })

        file_name = file_root + ext
        path = f"/tmp/{file_name}"

        with urllib.request.urlopen(request) as d:
            with open(path, mode="wb") as f:
                f.write(d.read())

        bucket = s3.Bucket(bucket)
        key = f"data/{file_name}"
        print(f"Save {path} to {key}")
        bucket.upload_file(path, key)
        uploaded.append(key)
        os.remove(path)

        print("Invoke ECS")
        response = ecs.run_task(
            cluster="default",
            launchType="FARGATE",
            taskDefinition="yans2019",
            count=1,
            platformVersion="LATEST",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": [
                        "subnet-xxxxxx"
                    ],
                    "assignPublicIp": "ENABLED"
                }
            },
            overrides={
                "containerOverrides": [{
                    "name": "yans2019",
                    "command": [
                        "--file_path",
                        key,
                        "--iteration",
                        iteration
                    ]
                }]
            }
            )

    return {
        "uploaded": uploaded
    }
