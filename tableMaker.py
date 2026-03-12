import boto3

dynamodb = boto3.client("dynamodb", region_name="us-east-1")

existing_tables = dynamodb.list_tables()["TableNames"]

if "users" not in existing_tables:
    dynamodb.create_table(
        TableName="users",
        KeySchema=[
            {"AttributeName": "username", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "username", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    print("users table created")
else:
    print("users table already exists")


if "links" not in existing_tables:
    dynamodb.create_table(
        TableName="links",
        KeySchema=[
            {"AttributeName": "username", "KeyType": "HASH"},
            {"AttributeName": "link_id", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "username", "AttributeType": "S"},
            {"AttributeName": "link_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    print("links table created")
else:
    print("links table already exists")
