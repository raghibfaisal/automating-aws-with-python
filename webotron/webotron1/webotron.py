import boto3
import click


session = boto3.Session(profile_name='python_automation')
s3 = session.resource('s3')


@click.group()
def cli():
    pass

@cli.command('list-buckets')
def list_buckets():
    "List all S3 buckets"
    for bucket in s3.buckets.all():
        print(bucket)

@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


if __name__ == "__main__":
    cli()
