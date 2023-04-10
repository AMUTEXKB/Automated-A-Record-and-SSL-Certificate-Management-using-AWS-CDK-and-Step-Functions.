import boto3
import json
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def lambda_handler(event, context):
    if os.environ.get("StateMachine") is not None:
        StateMachine= os.environ.get("StateMachine")
    else:
        error_message = "Missing environment variable StateMachine"
        logger.error(error_message)
        raise Exception(error_message)
    # Log the event
    logger.info(f"Received event: {json.dumps(event)}")

    # Parse the outer JSON object
    event_body = event['body']

    # Create a Step Functions client
    sfn_client = boto3.client('stepfunctions')
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']

    # Start the Step Function execution
    response = sfn_client.start_execution(
        stateMachineArn=f'arn:aws:states:us-east-1:{account_id}:stateMachine:{StateMachine}',
        input=event_body
    )

    # Log the Step Function execution ARN
    logger.info(f'Started Step Function execution: {response["executionArn"]}')

    # Return the Step Function execution ARN and the event to the API Gateway
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'executionArn': response['executionArn'],
            'event': event_body
        })
    }
