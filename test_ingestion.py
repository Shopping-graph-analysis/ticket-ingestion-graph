
import unittest
from unittest.mock import MagicMock, patch
import sys
import json

# Mock modules before import
sys.modules['boto3'] = MagicMock()
sys.modules['neo4j'] = MagicMock()

import main

class TestIngestion(unittest.TestCase):
    
    @patch('main.s3_client')
    @patch('main.driver')
    def test_ingestion_success(self, mock_driver, mock_s3):
        # Setup Mock S3
        csv_content = "ticket_id,basket_id,timestamp,product,category,quantity,store\n" \
                      "TCK-1,BASK-1,2025-01-01 10:00:00,Coffee,Drinks,1,Store-A\n"
        
        mock_body = MagicMock()
        mock_body.read.return_value = csv_content.encode('utf-8')
        mock_s3.get_object.return_value = {'Body': mock_body}
        
        # Setup Mock Neo4j
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        # Setup Input Event
        s3_event_payload = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "tickets.csv"}
                }
            }]
        }
        
        sqs_event = {
            "Records": [{
                "body": json.dumps(s3_event_payload)
            }]
        }
        
        # Run
        main.main(sqs_event, None)
        
        # Verify S3 call
        mock_s3.get_object.assert_called_with(Bucket='test-bucket', Key='tickets.csv')
        
        # Verify Neo4j call
        self.assertTrue(mock_session.run.called)
        args, kwargs = mock_session.run.call_args
        
        self.assertEqual(kwargs['ticket_id'], 'TCK-1')
        self.assertEqual(kwargs['product'], 'Coffee')
        self.assertEqual(kwargs['quantity'], '1')
        
        print("✅ Test Ingestion Success: Verified S3 read and Neo4j write calls.")

if __name__ == '__main__':
    unittest.main()
