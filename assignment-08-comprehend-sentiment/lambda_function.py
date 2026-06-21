import os

import boto3

comprehend = boto3.client('comprehend')


def lambda_handler(event, context):
  review = event.get('review') or event.get('text')
  if not review:
    return {'statusCode': 400, 'body': {'error': 'review text is required'}}

  response = comprehend.detect_sentiment(Text=review, LanguageCode='en')
  sentiment = response['Sentiment']
  scores = response['SentimentScore']

  print(f'Review: {review}')
  print(f'Sentiment: {sentiment}')
  print(f'Scores: {scores}')

  return {
    'statusCode': 200,
    'body': {
      'review': review,
      'sentiment': sentiment,
      'scores': scores,
    },
  }
