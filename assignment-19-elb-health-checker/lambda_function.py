import os

import boto3

elbv2 = boto3.client('elbv2')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
TARGET_GROUP_ARN = os.environ.get('TARGET_GROUP_ARN')


def lambda_handler(event, context):
  target_group_arn = event.get('target_group_arn') or TARGET_GROUP_ARN
  sns_topic_arn = event.get('sns_topic_arn') or SNS_TOPIC_ARN

  if not target_group_arn or not sns_topic_arn:
    return {
      'statusCode': 400,
      'body': {'error': 'target_group_arn and SNS_TOPIC_ARN are required'},
    }

  response = elbv2.describe_target_health(TargetGroupArn=target_group_arn)
  unhealthy_targets = []

  for target in response['TargetHealthDescriptions']:
    state = target['TargetHealth']['State']
    target_id = target['Target']['Id']
    reason = target['TargetHealth'].get('Reason', '')

    if state != 'healthy':
      unhealthy_targets.append({
        'target_id': target_id,
        'state': state,
        'reason': reason,
      })
      print(f'Unhealthy target: {target_id} ({state}) - {reason}')

  if unhealthy_targets:
    lines = [
      f"- {item['target_id']}: {item['state']} ({item['reason']})"
      for item in unhealthy_targets
    ]
    message = 'Unhealthy ELB targets detected:\n' + '\n'.join(lines)
    sns.publish(
      TopicArn=sns_topic_arn,
      Subject='ELB Health Check Alert',
      Message=message,
    )
    print(message)

  return {
    'statusCode': 200,
    'body': {
      'unhealthy_targets': unhealthy_targets,
      'alert_sent': bool(unhealthy_targets),
    },
  }
