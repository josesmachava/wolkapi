"""wolk URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import json
import os

import boto3
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI, File
from ninja.files import UploadedFile
import random
import string


def get_random_string(length):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    # print random string
    return result_str


api = NinjaAPI()


@api.post("/upload")
def upload(request, file: UploadedFile = File(...)):
    s3 = boto3.client('s3',
                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                      region_name="us-east-1"
                      )
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')

    name = get_random_string(8).lower()
    print(name.lower())
    with open('index.html', 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    bucket_name = f"{name}"
    s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'})
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'AddPerm',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': "arn:aws:s3:::%s/*" % bucket_name
        }]
    }
    bucket_policy = json.dumps(bucket_policy)
    s3.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)
    s3.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration={
            'ErrorDocument': {'Key': 'error.html'},
            'IndexDocument': {'Suffix': 'index.html'},
        })
    s3.upload_file("index.html", bucket_name, "index.html",
                   ExtraArgs={
                       'ACL': 'public-read',
                       'ContentType': 'text/html'

                   }
                   )
    website_url = f'https://{name}.s3-website.eu-central-1.amazonaws.com'
    data = file.read()
    return {
        "url": website_url

    }


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
