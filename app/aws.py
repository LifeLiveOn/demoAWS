import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

users_table = dynamodb.Table('users')
links_table = dynamodb.Table('links')

s3 = boto3.client('s3', region_name='us-east-1')
