from minio import Minio, ResponseError
import pickle


class MinioRepository:
    def __init__(self, url, access_key, secret_key):
        self.url = url
        self.access_key = access_key
        self.secret_key = secret_key
        self.client = Minio(self.url, access_key=self.access_key, secret_key=self.secret_key, secure=False)

    def get_model_from_bucket(self, model_uid, bucket_name):
        try:
            data = self.client.get_object(bucket_name, model_uid)
            result = pickle.loads(data.read())
        except Exception as e:
            raise Exception("Could not fetch data from bucket - {}".format(e))

        return result
