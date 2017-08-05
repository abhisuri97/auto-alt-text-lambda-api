# Auto Alt Text Lamdba API

This repository contains the code for the API backing the Auto Alt Text chrome extension. 

## Working API Link + Usage

This API link is working as of Aug 5 2017. 

```
http://im2txt-api-dev.us-west-2.elasticbeanstalk.com/predict
```

### Usage
The URL accepts a single query parameter `url` with the link to the image you wish to analyze.

#### Example:
Request:

```
http://im2txt-api-dev.us-west-2.elasticbeanstalk.com/predict?url=https://hack4impact.org/assets/images/photos/mayors-awards.jpg
```

Response:
```
[
  {
    "captions": [
      {
        "prob": "0.005958", 
        "sentence": "a group of people standing next to each other ."
      }, 
      {
        "prob": "0.002934", 
        "sentence": "a group of people posing for a picture ."
      }, 
      {
        "prob": "0.002054", 
        "sentence": "a group of people posing for a picture"
      }
    ], 
    "url": "https://hack4impact.org/assets/images/photos/mayors-awards.jpg"
  }
]
```

## Purpose

The purpose of the Auto Alt Text API is to generate captions for scenes with the im2txt model.
Additionally, this API can generate captions in < 5 seconds on a Lambda instance.

## Get it running

Create a docker instance and clone files from this repository into that instance. Note that all these files are using Python2.7 as the standard python version.

The entry file for this project is `application.py`. All necessary modules have been provided
except for boto3 which is part of the standard AWS Lambda runtime. This can be installed via pip

```
pip install boto3
```

Log into your AWS account and create an S3 bucket named `auto-alt-lamdba` (you can alter the name of your s3 bucket as long as you change line 73 in `application.py`. 

Next, download the zip file containing the pared down trained im2txt model from [Google Drive](https://drive.google.com/open?id=0B7qP_oLCzzHeZFBwX3AxbFlVc0E)

Lastly, you will need to create an AWS Lambda instance with the following characteristics

```
Runtime = Python 2.7
Handler = application.predict
Role = (see next section)

Advanced Settings
Memory (MB) = 1344 MB
Timeout = 1 min
```

Note: To keep the tensorflow model loaded into memory, it would be beest o create a cloudwatch event to ping the model every 5 minutes or so. 

### Creating an IAM policy role

In order to have the Lambda app pull the model.zip file from S3, it is necessary to give permissions for S3 to access the bucket. Additionally, to keep the application "warm" the role will need access to CloudWatch logs. Lastly, it will need limited Lambda Write functionality. The following is my policy summary as of Aug 5 2017.

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "IAmNotSureIfThisIsUniqueButIAmHidingIt",
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "arn:aws:s3:::auto-alt-lambda",
                "arn:aws:s3:::auto-alt-lambda/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```

