# Notte
A Discord bot that provides information about Dragalia Lost, a mobile game developed by Cygames and published by Nintendo.

## Prerequisites
* Python 3.7
* Amazon S3 bucket in which to store configuration data
* AWS access key, used to get and put objects in your S3 bucket
* Discord bot user

## Installing

Perform all of the following steps in the environment you will be using to run the bot.

1. Download all required packages using pip

    ```
    pip install -r requirements.txt
    ```
    
2. Store the following values as environment variables in the bot environment:

    | Environment Variable | Value Description |
    | --- | --- |
    | DISCORD_CLIENT_TOKEN | Your discord bot user's client token |
    | AWS_ACCESS_KEY_ID | Part of your AWS credentials |
    | AWS_SECRET_ACCESS_KEY | Part of your AWS credentials |
    | S3_BUCKET_NAME | Name of your S3 bucket |
    | WRITEABLE_CONFIG_KEY | Key of the writeable config object in your S3 bucket |
    | GUILD_CONFIG_KEY | Key of the guild config object in your S3 bucket |
    
    [More info about AWS access keys](https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys)
    
    [More info about S3 Buckets and Keys](https://docs.aws.amazon.com/AmazonS3/latest/dev/Introduction.html#CoreConcepts)

3. Run main.py using python 3
    
    ```
    python3 ./src/main.py
    ```
