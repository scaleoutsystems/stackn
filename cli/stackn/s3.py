import io

from minio import Minio
from minio.error import S3Error

def create_client(config, secure_mode=True):
    try:
        access_key = config['access_key']
    except Exception:
        print("No access key in S3 config.")
        return []
    try:
        secret_key = config['secret_key']
    except Exception:
        print("No secret key in S3 config.")
        return []

    if not secure_mode:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        from urllib3.poolmanager import PoolManager
        manager = PoolManager(num_pools=100, cert_reqs='CERT_NONE', assert_hostname=False)
        client = Minio(config['host'],
                            access_key=access_key,
                            secret_key=secret_key,
                            http_client=manager)
    else:
        minio_url = "{}".format(config['host'])
        client = Minio(minio_url,
                            access_key=access_key,
                            secret_key=secret_key)

    return client

def set_artifact(instance_name, instance, bucket, config, is_file=False, secure_mode=True):
    """ Instance must be a byte-like object. """
    client = create_client(config, secure_mode)
    found = client.bucket_exists(bucket)
    if not found:
        try:
            client.make_bucket(bucket)
        except Exception as err:
            print('Bucket does not exist, and failed to create bucket.')
            return False

    if is_file == True:
        client.fput_object(bucket, instance_name, instance)
    else:
        try:
            client.put_object(bucket, instance_name, io.BytesIO(instance), len(instance))
        except Exception as e:
            raise Exception("Could not load data into bytes {}".format(e))

    return True

