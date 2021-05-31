from .models import Model
from minio import Minio
import s3fs
from portal.models import PublicModelObject, PublishedModel

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