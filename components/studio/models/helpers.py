from .models import Model
from minio import Minio
from portal.models import PublicModelObject, PublishedModel

import io
import s3fs

def add_pmo_to_publish(mdl, pmodel):
    print(mdl.name)
    print(mdl.version)

    host = mdl.s3.host
    access_key = mdl.s3.access_key
    secret_key = mdl.s3.secret_key
    bucket = mdl.bucket
    region = mdl.s3.region
    filename = mdl.uid
    try:
        s3 = s3fs.S3FileSystem(
            key=access_key,
            secret=secret_key,
            client_kwargs={
                'endpoint_url': 'https://'+host
            }
        )
    except Exception as err:
        print(err)
    print("Created S3 fs")
    try:
        fobj = s3.open(bucket+'/'+filename, 'rb')
    except Exception as err:
        print(err)
    print("Opened s3 file.")
    try:
        pmo = PublicModelObject(model=mdl)
        pmo.save()
        pmo.obj.save(filename, fobj)
    except Exception as err:
        print(err)

    print("Created public model object")
    pmodel.model_obj.add(pmo)


def get_download_url(model_id):
    model = Model.objects.get(pk=model_id)
    bucket = model.bucket
    path = model.path
    uid = model.uid

    minio_host = model.s3.host
    minio_access_key = model.s3.access_key
    minio_secret_key = model.s3.secret_key
    minio_region = model.s3.region

    download_url = ""
    try:
        client = Minio(
            minio_host,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            region=minio_region,
        )

        download_url = client.presigned_get_object(bucket, path + uid)
    except Exception as e:
        print(e)

    return download_url


# This Method use Minio Python API to create a minio client and connect it to a minio server instance
def create_client(S3_storage, secure_mode=True):
    try:
        access_key = S3_storage.access_key
    except Exception:
        print("No access key could be found with the current S3 storage instance: {}".format(S3_storage))
        return []
    try:
        secret_key = S3_storage.secret_key
    except Exception:
        print("No secret key could be found with the current S3 storage instance: {}".format(S3_storage))
        return []

    # API connection does not want scheme in the minio URL
    # Yet we need the URL to have the scheme included when some app charts use the minio client mc
    if 'http://' in S3_storage.host:
        minio_url = S3_storage.host.replace('http://', '')
    elif 'https://' in S3_storage.host:
        minio_url = S3_storage.host.replace('https://', '')
    else:
        minio_url = S3_storage.host

    if not secure_mode:
        client = Minio(minio_url, access_key=access_key, secret_key=secret_key, secure=secure_mode)
    else:
        client = Minio(minio_url, access_key=access_key, secret_key=secret_key)

    return client


# This Method use Minio Python API to save an artificat into a running minio server instance
def set_artifact(artifact_name, artifact_file, bucket, S3_storage, is_file=False, secure_mode=True):
    """ Instance must be a byte-like object. """
    client = create_client(S3_storage, secure_mode)
    found = client.bucket_exists(bucket)
    if not found:
        try:
            client.make_bucket(bucket)
        except Exception as err:
            print('Bucket does not exist, and failed to create bucket.')
            return False

    if is_file == True:
        client.fput_object(bucket, artifact_name, artifact_file)
    else:
        try:
            client.put_object(bucket, artifact_name, io.BytesIO(artifact_file), len(artifact_file))
        except Exception as e:
            raise Exception("Could not load data into bytes {}".format(e))

    return True