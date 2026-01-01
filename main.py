import json
import urllib.parse


import boto3
import csv
import io
import os
from neo4j import GraphDatabase

s3_client = boto3.client('s3')

# Neo4j Configuration
NEO4J_URI = os.getenv('NEO4J_URI') # e.g., "bolt://localhost:7687"
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# Initialize driver only if credentials are present (to avoid errors during local non-integration tests)
driver = None
if NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_full_path(s3_record):
    bucket_name = s3_record['s3']['bucket']['name']
    object_key = s3_record['s3']['object']['key']
    # S3 keys can be URL encoded (e.g. spaces as + or %20)
    object_key = urllib.parse.unquote_plus(object_key)
    
    return f"s3://{bucket_name}/{object_key}", bucket_name, object_key

def ingest_tickets(bucket, key):
    if not driver:
        print("Neo4j driver not initialized. Skipping ingestion.")
        return

    print(f"Reading file from S3: {bucket}/{key}")
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(content))
        
        with driver.session() as session:
            for row in csv_reader:
                # row keys: ticket_id,basket_id,timestamp,product,category,quantity,store
                transaction_query = """
                MERGE (t:Ticket {ticket_id: $ticket_id})
                ON CREATE SET t.timestamp = $timestamp, t.store = $store, t.basket_id = $basket_id
                
                MERGE (p:Product {name: $product})
                ON CREATE SET p.category = $category
                
                MERGE (t)-[r:CONTAINS]->(p)
                SET r.quantity = toInteger($quantity)
                """
                
                session.run(transaction_query, 
                            ticket_id=row['ticket_id'],
                            basket_id=row['basket_id'],
                            timestamp=row['timestamp'],
                            product=row['product'],
                            category=row['category'],
                            quantity=row['quantity'],
                            store=row['store'])
                            
        print(f"Successfully ingested tickets from {key}")

    except Exception as e:
        print(f"Error ingesting file {bucket}/{key}: {e}")

def main(event, context):
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
                                full_path, bucket, key = get_full_path(s3_record)
                                extracted_paths.append(full_path)
                                print(f"File uploaded: {full_path}")
                                
                                # Trigger ingestion
                                ingest_tickets(bucket, key)
                                
                except json.JSONDecodeError as e:
                    print(f"Error decoding SQS body: {e}")
                except KeyError as e:
                    print(f"Error parsing S3 event structure: {e}")
                    
    return extracted_paths
