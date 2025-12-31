import json
import main

def test_sqs_s3_extraction():
    # Mock SQS event containing an S3 event notification
    # The 'body' field in SQS is a stringified JSON of the S3 event
    
    s3_event_payload = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2024-01-01T12:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {
                        "name": "my-test-bucket",
                        "arn": "arn:aws:s3:::my-test-bucket"
                    },
                    "object": {
                        "key": "uploads/test+file.txt",
                        "size": 1024,
                        "eTag": "d41d8cd98f00b204e9800998ecf8427e"
                    }
                }
            }
        ]
    }
    
    sqs_event = {
        "Records": [
            {
                "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
                "receiptHandle": "MessageReceiptHandle",
                "body": json.dumps(s3_event_payload),
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1523232000000",
                    "SenderId": "123456789012",
                    "ApproximateFirstReceiveTimestamp": "1523232000001"
                },
                "messageAttributes": {},
                "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                "awsRegion": "us-east-1"
            }
        ]
    }

    print("Testing SQS -> S3 Event Extraction...")
    extracted = main.lambda_handler(sqs_event, None)
    
    expected_path = "s3://my-test-bucket/uploads/test file.txt"
    
    if expected_path in extracted:
        print("✅ SUCCESS: Correctly extracted path:")
        print(f"   Found: {extracted[0]}")
    else:
        print("❌ FAILED: Did not find expected path.")
        print(f"   Expected: {expected_path}")
        print(f"   Got: {extracted}")

if __name__ == "__main__":
    test_sqs_s3_extraction()
