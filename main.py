import json
import urllib.parse

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    extracted_paths = []
    
    if 'Records' in event:
        for record in event['Records']:
            # SQS body is a string literal containing the S3 event
            body = record.get('body')
            if body:
                try:
                    s3_event = json.loads(body)
                    if 'Records' in s3_event:
                        for s3_record in s3_event['Records']:
                            if 's3' in s3_record:
                                bucket_name = s3_record['s3']['bucket']['name']
                                object_key = s3_record['s3']['object']['key']
                                # S3 keys can be URL encoded (e.g. spaces as + or %20)
                                object_key = urllib.parse.unquote_plus(object_key)
                                
                                full_path = f"s3://{bucket_name}/{object_key}"
                                extracted_paths.append(full_path)
                                print(f"File uploaded: {full_path}")
                except json.JSONDecodeError as e:
                    print(f"Error decoding SQS body: {e}")
                except KeyError as e:
                    print(f"Error parsing S3 event structure: {e}")
                    
    return extracted_paths
