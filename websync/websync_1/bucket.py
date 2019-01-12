#!/usr/bin/python
""" Classes for s3 buckets."""
from pathlib import Path
import mimetypes
from functools import reduce

import boto3
from botocore.exceptions import ClientError

from hashlib import md5
from websync_1 import util

class BucketManager:
    """Manage an s3 bucket."""

    CHUNK_SIZE = 8388608


    def __init__(self, session):
        """Create an object for bucket manager."""
        self.s3 = session.resource('s3')
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNK_SIZE,
            multipart_threshold=self.CHUNK_SIZE
        )
        self.manifest = {}


    def get_bucket(self, bucket_name):
        """Get a bucket by name."""
        return self.s3.Bucket(bucket_name)


    def get_region_name(self,bucket):
        """Returns the region in which this bucket is in."""
        bucket_location = self.s3.meta.client.get_bucket_location(Bucket=bucket.name)
        return bucket_location["LocationConstraint"] or "us-east-1"


    def get_bucket_url(self,bucket):
        """Get the url for this bucket."""
        return "http://{}.{}".format(bucket.name, util.get_endpoint(self.get_region_name(bucket)).host)


    def all_buckets(self):
        """Retruns all buckets."""
        return self.s3.buckets.all()


    def all_objects(self, bucket):
        """Returns all objects of an s3 bucket"""
        return self.s3.Bucket(bucket).objects.all()

    def initialize_bucket(self, bucket_name):
        """Create and setup an s3 bucket."""
        s3_bucket = None
        try:
            s3_bucket = self.s3.create_bucket(Bucket=bucket_name)
        except ClientError as error:
            if error.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                raise error
        return s3_bucket

    def set_policy(self, bucket):
        """Sets the policy for static website hosting."""
        policy = """
        {
         "Version": "2012-10-17",
         "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::%s/*"
            }]
        }""" %bucket.name
        policy = policy.strip()
        pol = bucket.Policy()
        pol.put(Policy=policy)


    def web_configure(self, bucket):
        """COnfigures the bucket for Static Website Hosting."""
        bucket.Website().put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'},
            'IndexDocument': {
                'Suffix': 'index.html'}
            })


    def load_manifest(self, bucket):
        """Load manifest for caching."""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']]=obj['ETag']


    @staticmethod
    def has_data(data):
        """Generate md5 hash for data."""
        hash = md5()
        hash.update(data)
        return hash


    def gen_etag(self, path):
        """Generate Etag for file."""
        hashes = []
        with open(path, 'rb') as f:
            while True:
                data = f.read(self.CHUNK_SIZE)

                if not data:
                    break
            hashes.append(self.has_data(data))
        if not hashes:
            return
        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            hash = self.hash_data(reduce(lambda x,y: x+y, (h.digest for h in hashes)))
            return '"{}-{}"'.format(hash.hexdigest(),len(hashes))


    def upload_file(self, bucket, path, key):
        """Upload files to s3 Bucket."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        etag = self.gen_etag(path)
        if self.manifest.get(key, '') == etag:
            return

        return bucket.upload_file(path, key, ExtraArgs={'ContentType': content_type},Config=self.transfer_config)


    def sync_bucket(self, pathname, bucket_name):
            bucket = self.s3.Bucket(bucket_name)
            self.load_manifest(bucket)
            root = Path(pathname).expanduser().resolve()

            def handle_directory(target):
                for p in target.iterdir():
                    if p.is_dir():
                        handle_directory(p)
                    if p.is_file():
                        self.upload_file(bucket, str(p), str(p.relative_to(root)))
            handle_directory(root)
