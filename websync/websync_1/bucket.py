""" Classes for s3 buckets."""
from pathlib import Path
import mimetypes
from botocore.exceptions import ClientError

class BucketManager:
    """Manage an s3 bucket."""
    def __init__(self, session):
        "Creat and object for bucket manager"
        self.s3 = session.resource('s3')
        pass


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


    @staticmethod
    def upload_file(bucket, path, key):
        """Upload files to s3 Bucket."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        return bucket.upload_file(path, key, ExtraArgs={'ContentType': content_type})


    def sync_bucket(self, pathname, bucket_name):
            bucket = self.s3.Bucket(bucket_name)
            root = Path(pathname).expanduser().resolve()

            def handle_directory(target):
                for p in target.iterdir():
                    if p.is_dir():
                        handle_directory(p)
                    if p.is_file():
                        self.upload_file(bucket, str(p), str(p.relative_to(root)))
            handle_directory(root)
