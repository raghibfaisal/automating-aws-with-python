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
from domain import DomainManager
import util

session = None
bucket_manager = None
domain_manager = None


@click.group()
@click.option('--profile', default=None, help='Use AWS profile')
def cli(profile):
    global session, bucket_manager, domain_manager
    session_cfg = {}
    if profile:
        session_cfg['profile_name']=profile

    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)
    domain_manager = DomainManager(session)
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
    print(bucket_manager.get_bucket_url(bucket_manager.s3.Bucket(bucket)))


@cli.command('setup-domain')
@click.argument('domain')
def setup_domain(domain):
    """Configure domain to point to bucket."""
    bucket = bucket_manager.get_bucket(domain)
    zone = domain_manager.find_hosted_zone(domain) or domain_manager.create_hosted_zone(domain)
    endpoint = util.get_endpoint(bucket_manager.get_region_name(bucket))
    domain_manager.create_s3_domain_record(zone, domain, endpoint)
    print("Domain configure: http://{}".format(domain))

if __name__ == "__main__":
    cli()
