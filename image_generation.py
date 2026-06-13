import json
import boto3
import botocore
from datetime import datetime
import base64
def lambda_handler(event, context):
    event = json.loads(event['body'])
    message = event['message']
    bedrock = boto3.client("bedrock-runtime",region_name="us-west-2",config = botocore.config.Config(read_timeout=300, retries = {'max_attempts':3}))
    s3 = boto3.client('s3')
    payload = {  # CHANGED: SDXL payload (text_prompts/cfg_scale/seed/steps) replaced with SD3.5 Large format
        "prompt": message,
        "mode": "text-to-image",
        "aspect_ratio": "1:1",
        "output_format": "png"
    }
    response = bedrock.invoke_model(body=json.dumps(payload),modelId = 'stability.sd3-5-large-v1:0',contentType = "application/json",accept = "application/json")  # CHANGED: modelId from retired stability.stable-diffusion-xl-v0 to active stability.sd3-5-large-v1:0
    response_body = json.loads(response.get("body").read())
    base_64_img_str = response_body["images"][0]  # CHANGED: SD3.5 returns base64 under ["images"][0] instead of ["artifacts"][0]["base64"]
    image_content = base64.decodebytes(bytes(base_64_img_str,"utf-8"))
    bucket_name = 'bedrock-course-bucket'
    current_time = datetime.now().strftime('%H%M%S')
    s3_key = f"output-images/{current_time}.png"
    s3.put_object(Bucket = bucket_name, Key = s3_key, Body = image_content, ContentType = 'image/png')
    return {
        'statusCode': 200,
        'body': json.dumps('Image Saved to s3')
    }
