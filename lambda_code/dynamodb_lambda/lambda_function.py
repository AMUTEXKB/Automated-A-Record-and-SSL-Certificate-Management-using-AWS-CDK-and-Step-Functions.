import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table_name=os.environ.get("table_name")
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    # Save event data to DynamoDB table
    table.put_item(Item=event)
    
    # Pass event to next Lambda function in Step Function
    return {
        'statusCode': 200,
        'event': event
    }