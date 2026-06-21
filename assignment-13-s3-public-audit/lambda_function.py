import os

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
PUBLIC_URI = 'http://acs.amazonaws.com/groups/global/AllUsers'


def is_bucket_public(bucket_name):
  try:
    policy_status = s3.get_bucket_policy_status(Bucket=bucket_name)
    if policy_status['PolicyStatus']['IsPublic']:
      return True
  except ClientError:
    pass

  try:
    public_access = s3.get_public_access_block(Bucket=bucket_name)
    config = public_access['PublicAccessBlockConfiguration']
    if not all([
      config.get('BlockPublicAcls', False),
      config.get('IgnorePublicAcls', False),
      config.get('BlockPublicPolicy', False),
      config.get('RestrictPublicBuckets', False),
    ]):
      return True
  except ClientError:
    pass

  try:
    acl = s3.get_bucket_acl(Bucket=bucket_name)
    for grant in acl.get('Grants', []):
      grantee = grant.get('Grantee', {})
      if grantee.get('URI') == PUBLIC_URI:
        return True
  except ClientError:
    pass

  return False


def lambda_handler(event, context):
  sns_topic_arn = event.get('sns_topic_arn') or SNS_TOPIC_ARN
  if not sns_topic_arn:
    return {'statusCode': 400, 'body': {'error': 'SNS_TOPIC_ARN is required'}}

  public_buckets = []

  for bucket in s3.list_buckets()['Buckets']:
    bucket_name = bucket['Name']
    if is_bucket_public(bucket_name):
      public_buckets.append(bucket_name)
      print(f'Public bucket detected: {bucket_name}')

  if public_buckets:
    message = 'Public S3 buckets detected:\n' + '\n'.join(public_buckets)
    sns.publish(
      TopicArn=sns_topic_arn,
      Subject='Public S3 Bucket Audit Alert',
      Message=message,
    )
    print(message)

  return {
    'statusCode': 200,
    'body': {
      'public_buckets': public_buckets,
      'alert_sent': bool(public_buckets),
    },
  }
