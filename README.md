# turbo-carnival
Visualizes [Rocket League](http://www.rocketleaguegame.com/) Replays

[Upload and watch Rocket League replays here](http://rocketleague.carlosrendon.me/)

## Deployment Instructions

This application uses the following AWS services:
- S3
- Elastic Beanstalk
- DynamoDB

First you must have an AWS account, and create an S3 bucket. You will
need to update `application.py` with your S3 bucket name.

You also must create a DynamoDB table `turbo-carnival` with partition_key of `replay_key`. 
Application assumes you will use region `us-west-2`.

App is deployed using eb cli tool and also requires the AWS cli
tool. These can be installed using pip.

```bash
python -m pip install awscli
python -m pip install --upgrade --user awsebcli
```

You need to configure the AWS cli with API keys and which region you
want to work in.

```bash
aws configure
```

The first time you deploy the app, you have the create the environment
in Elastic Beanstalk.

```bash
cd website
eb create [environment-name]
```

You need to use IAM to give the Elastic Beanstalk role read and write
permissions to your S3 bucket.

Deployment to an existing Elastic Beanstalk is easy:

```bash
cd website
eb deploy
```

## Local Deploynment

The application can also be run locally. App assumes `/tmp` or
`c:\tmp` exists and is writable. Don't worry it only uses it
temporarily. The application still requires an S3 bucket when run
locally. It also requires the
[octane](https://github.com/tfausak/octane/releases/latest) to be in
your PATH.

```bash
cd website
python application.py
```
