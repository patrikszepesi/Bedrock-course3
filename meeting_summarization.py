import boto3
import botocore.config
import json
import base64
from datetime import datetime
from email import message_from_bytes


def extract_text_from_multipart(data):
    msg = message_from_bytes(data)

    text_content = ''

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                text_content += part.get_payload(decode=True).decode('utf-8') + "\n"

    else:
        if msg.get_content_type() == "text/plain":
            text_content = msg.get_payload(decode=True).decode('utf-8')

    return text_content.strip() if text_content else None


def generate_summary_from_bedrock(content:str) ->str:
    prompt_text = f"""Human: Summarize the following meeting notes: {content}
    Assistant:"""

    body = {
        "prompt":prompt_text,
        "max_tokens_to_sample":5000,
        "temperature":0.1,
        "top_k":250,
        "top_p":0.2,
        "stop_sequences": ["\n\nHuman:"]
    }

    try:
        bedrock = boto3.client("bedrock-runtime",region_name="us-west-2",config = botocore.config.Config(read_timeout=300, retries = {'max_attempts':3}))
        response = bedrock.invoke_model(body=json.dumps(body),modelId="anthropic.claude-v2")
        response_content = response.get('body').read().decode('utf-8')
        response_data = json.loads(response_content)
        summary = response_data["completion"].strip()
        return summary

    except Exception as e:
        print(f"Error generating the summary: {e}")
        return ""

def save_summary_to_s3_bucket(summary, s3_bucket, s3_key):

    s3 = boto3.client('s3')

    try:
        s3.put_object(Bucket = s3_bucket, Key = s3_key, Body = summary)
        print("Summary saved to s3")

    except Exception as e:
        print("Error when saving the summary to s3")


def lambda_handler(event,context):

    decoded_body = base64.b64decode(event['body'])

    text_content = extract_text_from_multipart(decoded_body)

    if not text_content:
        return {
            'statusCode':400,
            'body':json.dumps("Failed to extract content")
        }


    summary = generate_summary_from_bedrock(text_content)

    if summary:
        current_time = datetime.now().strftime('%H%M%S') #UTC TIME, NOT NECCESSARILY YOUR TIMEZONE
        s3_key = f'summary-output/{current_time}.txt'
        s3_bucket = 'bedrock-course-bucket'

        save_summary_to_s3_bucket(summary, s3_bucket, s3_key)

    else:
        print("No summary was generated")


    return {
        'statusCode':200,
        'body':json.dumps("Summary generation finished")
    }

    
