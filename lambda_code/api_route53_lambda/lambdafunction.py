import boto3

def lambda_handler(event, context):
    # Extract the business name from the event data
    business_name = event['business_name']
    domain= os.environ.get("domain")
    hostedzoneid=os.environ.get("hostedzone")
    # Connect to the Route53 client
    client = boto3.client('route53')

    # Create a new A record in the domain
    response = client.change_resource_record_sets(
        HostedZoneId=hostedzoneid,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': business_name + '.' + domain,
                        'Type': 'A',
                        'TTL': 300,
                        'ResourceRecords': [
                            {
                                'Value': '<IP address>'
                            }
                        ]
                    }
                }
            ]
        }
    )

    return response
