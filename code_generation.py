import boto3
import botocore.config
import json
from datetime import datetime


def generate_code_using_bedrock(message:str,language:str) ->str:

    prompt_text = f"""
Human: Write {language} code for the following instructions: {message}.
    Assistant:
    """
    body = {
        "prompt": prompt_text,
        "max_tokens_to_sample": 2048,
        "temperature": 0.1,
        "top_k":250,
        "top_p": 0.2,
        "stop_sequences":["\n\nHuman:"]
    }

    try:
        bedrock = boto3.client("bedrock-runtime",region_name="us-west-2",config = botocore.config.Config(read_timeout=300, retries = {'max_attempts':3}))
        response = bedrock.invoke_model(body=json.dumps(body),modelId="anthropic.claude-v2")
        response_content = response.get('body').read().decode('utf-8')
        response_data = json.loads(response_content)
        code = response_data["completion"].strip()
        return code

    except Exception as e:
        print(f"Error generating the code: {e}")
        return ""

def save_code_to_s3_bucket(code, s3_bucket, s3_key):

    s3 = boto3.client('s3')

    try:
        s3.put_object(Bucket = s3_bucket, Key = s3_key, Body = code)
        print("Code saved to s3")

    except Exception as e:
        print("Error when saving the code to s3")

def lambda_handler(event, context):
    event = json.loads(event['body'])
    message = event['message']
    language = event['key']
    print(message, language)

    generated_code = generate_code_using_bedrock(message, language)

    if generated_code:
        current_time = datetime.now().strftime('%H%M%S')
        s3_key = f'code-output/{current_time}.py'
        s3_bucket = 'bedrock-course-bucket'

        save_code_to_s3_bucket(generated_code,s3_bucket,s3_key)

    else:
        print("No code was generated")

    return {
        'statusCode':200,
        'body':json.dumps('Code generation ')

    }
