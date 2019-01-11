#!/usr/bin/python

"""
WEBSYNC : Deploy websites with AWS.

Automates the process of deploying static websites to AWS
Features -
- Create buckets
- Setup buckets
- Syncs local directory with S3
- Configures DNS with AWS Route53
- Configures CDN with AWS CloudFront
"""


import boto3
import click
from bucket import BucketManager


session = boto3.Session(profile_name='python_automation')
bucket_manager = BucketManager(session)


@click.group()
def cli():

    pass


@cli.command('list-buckets')
def list_buckets():
    """List all S3 buckets."""
    for bucket in bucket_manager.all_buckets():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List all buckets in AWS s3."""
    for obj in bucket_manager.all_objects(bucket):
        print(obj)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """To configure s3 bucket."""
    s3_bucket = bucket_manager.initialize_bucket(bucket)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.web_configure(s3_bucket)
    return


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents on pathname to s3 Bucket."""
    bucket_manager.sync_bucket(pathname, bucket)


if __name__ == "__main__":
    cli()
