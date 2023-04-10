import boto3

def lambda_handler(event, context):
    # Retrieve domain name from event
    domain_name = event['domain_name']
    
    # Initialize Route53 client
    client = boto3.client('route53')
    
    # Create Route53 hosted zone for domain
    response = client.create_hosted_zone(
        Name=domain_name,
        CallerReference=str(hash(domain_name)),
        HostedZoneConfig={
            'Comment': 'Hosted zone for ' + domain_name,
            'PrivateZone': False
        }
    )
    
    # Extract hosted zone ID from response
    hosted_zone_id = response['HostedZone']['Id']
    
    # Retrieve Dukaan's IP address for CNAME record
    dukaan_ip = event['ip_address']  # Replace with Dukaan's IP address
    
    # Create CNAME record for domain
    response = client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': 'www.' + domain_name,
                        'Type': 'CNAME',
                        'TTL': 300,
                        'ResourceRecords': [
                            {
                                'Value': dukaan_ip
                            }
                        ]
                    }
                }
            ]
        }
    )

    # Create CNAME record for domain
    response = client.change_resource_record_sets(
        HostedZoneId=hosted_zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'CREATE',
                    'ResourceRecordSet': {
                        'Name': 'www.' + domain_name,
                        'Type': 'CNAME',
                        'TTL': 300,
                        'ResourceRecords': [
                            {
                                'Value': dukaan_ip
                            }
                        ]
                    }
                }
            ]
        }
    ) 
    
    # Initialize ACM client
    acm = boto3.client('acm')
    # Request SSL certificate for domain and alternate domain
    response = acm.request_certificate(
        DomainName=domain_name,
        SubjectAlternativeNames=[
            alternate_domain,
            'www.' + domain_name,
        ],
    )    
    # Return success message
    return {
        'statusCode': 200,
        'body': 'Hosted zone and CNAME record created successfully'
    }
