import io
import shutil
import tarfile

import s3fs
from django.apps import apps
from django.conf import settings
from minio import Minio

from .models import Model

PublicModelObject = apps.get_model(app_label=settings.PUBLICMODELOBJECT_MODEL)


def add_pmo_to_publish(mdl, pmodel):
    print(mdl.name)
    print(mdl.version)

    host = mdl.s3.host
    access_key = mdl.s3.access_key
    secret_key = mdl.s3.secret_key
    bucket = mdl.bucket
    filename = mdl.uid
    path = mdl.path
    # TODO: this is a quick bugfix, path for tensorflow models is "models",
    # it should contain the model uid
    if path == "models":
        path = filename
    try:
        s3 = s3fs.S3FileSystem(
            key=access_key,
            secret=secret_key,
            client_kwargs={"endpoint_url": "http://" + host},
        )
    except Exception as err:
        print(err)
    print("Created S3 fs")
    try:
        # if e.g tensorflow model, the object is already compressed
        if path == filename:
            fobj = s3.open(bucket + "/" + path, "rb")
        # else if model is e.g mlflow, the model artifact is a folder and
        # needs to be compressed
        else:
            # download files on folder inside bucket into tmp folder
            s3.get(bucket + "/" + path, "./tmp/", recursive=True)
            # create tar file
            with tarfile.open("model.tar", "w") as tar:
                tar.add("./tmp/")
            # remove tmp folder
            shutil.rmtree("./tmp")
            # open tar for later read
            fobj = open("./model.tar", "rb")

        print("Opened s3 file.")

        pmo = PublicModelObject(model=mdl)
        pmo.save()
        pmo.obj.save(filename, fobj)
        fobj.close()
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
    path = ""
    if model.object_type.slug == "mlflow":
        path = model.path
    try:
        client = Minio(
            minio_host,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            region=minio_region,
            secure=False,
        )

        download_url = client.presigned_get_object(bucket, path + uid)
    except Exception as e:
        print(e, flush=True)

    return download_url


# This Method use Minio Python API to create a minio client and
# connect it to a minio server instance
def create_client(S3_storage, secure_mode=True):
    try:
        access_key = S3_storage.access_key
    except Exception:
        print(
            (
                "No access key could be found with "
                "the current S3 storage instance: {}"
            ).format(S3_storage)
        )
        return []
    try:
        secret_key = S3_storage.secret_key
    except Exception:
        print(
            (
                "No secret key could be found with "
                "the current S3 storage instance: {}"
            ).format(S3_storage)
        )
        return []

    # API connection does not want scheme in the minio URL
    # Yet we need the URL to have the scheme included when
    # some app charts use the minio client mc
    if "http://" in S3_storage.host:
        minio_url = S3_storage.host.replace("http://", "")
    elif "https://" in S3_storage.host:
        minio_url = S3_storage.host.replace("https://", "")
    else:
        minio_url = S3_storage.host

    if not secure_mode:
        client = Minio(
            minio_url,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure_mode,
        )
    else:
        client = Minio(minio_url, access_key=access_key, secret_key=secret_key)

    return client


# This Method use Minio Python API to save an artificat
# into a running minio server instance
def set_artifact(
    artifact_name,
    artifact_file,
    bucket,
    S3_storage,
    is_file=False,
    secure_mode=True,
):
    """Instance must be a byte-like object."""
    client = create_client(S3_storage, secure_mode)

    try:
        found = client.bucket_exists(bucket)
    except Exception as err:
        print(err)
        print("EXCEPTION LOG: Client could not verify if bucket exists")
        return False

    if not found:
        try:
            client.make_bucket(bucket)
        except Exception as err:
            print(err)
            print("Bucket does not exist, and failed to create bucket.")
            return False

    if is_file:
        try:
            client.fput_object(bucket, artifact_name, artifact_file)
        except Exception as err:
            print(err)
            print("Client method fput_object failed")
            return False
    else:
        try:
            client.put_object(
                bucket,
                artifact_name,
                io.BytesIO(artifact_file),
                len(artifact_file),
            )
        except Exception as err:
            print(err)
            print("Client method put_object failed")
            return False

    return True
