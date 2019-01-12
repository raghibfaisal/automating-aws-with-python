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
from certificate import CertificateManager
from cdn import DistributionManager
import util

session = None
bucket_manager = None
domain_manager = None
cert_manager = None
dist_manager = None

@click.group()
@click.option('--profile', default=None, help='Use AWS profile')
def cli(profile):
    global session, bucket_manager, domain_manager, cert_manager, dist_manager
    session_cfg = {}
    if profile:
        session_cfg['profile_name']=profile

    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)
    domain_manager = DomainManager(session)
    cert_manager = CertificateManager(session)
    dist_manager = DistributionManager(session)
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
    print("Domain configured: http://{}".format(domain))


@cli.command('find-cert')
@click.argument('domain')
def find_cert(domain):
    """Find a certificate for domain."""
    print(cert_manager.find_matching_cert(domain))


@cli.command('setup-cdn')
@click.argument('domain')
@click.argument('bucket')
def setup_cdn(domain, bucket):
    """Setup a CDN."""
    dist = dist_manager.find_matching_dist(domain)
    if not dist:
        cert = cert_manager.find_matching_cert(domain)
        if not cert:
            print("ERROR: No matching cert found")
            return

        dist = dist_manager.create_dist(domain, cert)
        print("Waiting for distribution deployment...")
        dist_manager.await_deploy(dist)

    zone = domain_manager.find_hosted_zone(domain) or domain_manager.create_hosted_zone(domain)
    domain_manager.create_cf_domain_record(zone, domain, dist['DomainName'])
    print("Domain configured: https://{}".format(domain))

    return


if __name__ == "__main__":
    cli()
