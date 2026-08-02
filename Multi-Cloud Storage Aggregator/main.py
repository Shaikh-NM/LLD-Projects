class AWSS3SDK:
    def put_object_to_s3(self, bucket_name: str, key: str, payload: str) -> bool:
        pass

    def get_object_from_s3(self, bucket_name: str, key: str)->bytes:
        pass

    def remove_object_from_s3(self, bucket_name: str, key: str)->bool:
        pass

from abc import ABC, abstractmethod
class CloudStorageAdapter(ABC):
    @abstractmethod
    def upload_file(self, container_or_bucket: str, file_path: str, data: bytes)->bool:
        pass

    @abstractmethod
    def download_file(self, container_or_bucket: str, file_path: str)->bytes:
        pass

    @abstractmethod
    def delete_file(self, container_or_bucket: str, file_path: str)->bool:
        pass

class S3Adapter(CloudStorageAdapter):
    def __init__(self, sdk: AWSS3SDK):
        self._sdk: AWSS3SDK = sdk

    def upload_file(self, container_or_bucket, file_path, data)->bool:
        return self._sdk.put_object_to_s3(bucket_name=container_or_bucket, key=file_path, payload=data)

    def download_file(self, container_or_bucket, file_path):
        return self._sdk.download_file(container_or_bucket, file_path)

    def delete_file(self, container_or_bucket, file_path):
        return self._sdk.delete_file(container_or_bucket, file_path)

from enum import Enum
class CloudProvider(Enum):
    AWS_S3 = "AWS_S3"
    GCS = "GCS"
    AZURE_BLOB = "AZURE_BLOB"

from typing import Dict
class CloudStorageFactory:
    _adaptaper_cache: Dict[CloudProvider, CloudStorageAdapter] = {}    

    @classmethod
    def get_adapter(cls, provider: CloudProvider) -> CloudStorageAdapter:
        if provider not in cls._adaptaper_cache:
            if provider == CloudProvider.AWS_S3:
                cls._adaptaper_cache[provider] = S3Adapter(AWSS3SDK())
        return cls._adaptaper_cache[provider]

class MultiCloudStorageManager:
    def upload(self, provider: CloudProvider, destination: str, file_name: str, payload: bytes):
        adapter = CloudStorageFactory.get_adapter(provider)
        return adapter.upload_file(container_or_bucket=destination, file_path=file_name, data=payload)

