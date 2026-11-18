import json
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal
import boto3

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'joel-inventory-items'

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    processed_count = 0

    for record in event.get('Records', []):
        bucket_name = record['s3']['bucket']['name']
        object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])

        print(f"Memproses file: s3://{bucket_name}/{object_key}")

        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        raw_content = response['Body'].read().decode('utf-8')
        items = json.loads(raw_content, parse_float=Decimal)

        if isinstance(items, dict):
            items = [items]

        timestamp = datetime.now(timezone.utc).isoformat()

        with table.batch_writer() as batch:
            for item in items:
                if 'item_id' not in item:
                    continue
                item['last_updated'] = timestamp
                item['source_file'] = object_key
                batch.put_item(Item=item)
                processed_count += 1

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Inventory ingestion berhasil',
            'items_processed': processed_count
        })
    }