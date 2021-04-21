from .models import Model
from minio import Minio


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
