from functools import lru_cache
from pathlib import Path
from .config import settings


@lru_cache
def credential():
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential(managed_identity_client_id=settings().azure_client_id or None)


@lru_cache
def blob_client():
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient(settings().azure_storage_account_url, credential=credential())


def put(key, content, mime):
    if settings().app_mode == 'azure':
        from azure.storage.blob import ContentSettings
        blob_client().get_blob_client(settings().azure_storage_container,key).upload_blob(
            content, overwrite=False, content_settings=ContentSettings(content_type=mime))
    else:
        root = Path(settings().local_storage_path).resolve()
        path = (root/key).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Invalid storage key')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)


def get(key):
    if settings().app_mode == 'azure':
        return blob_client().get_blob_client(settings().azure_storage_container,key).download_blob().readall()
    root=Path(settings().local_storage_path).resolve()
    path=(root/key).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Invalid storage key')
    return path.read_bytes()


def notify(job_id):
    """Best-effort wake-up. SQL jobs are the durable source of truth; polling recovers lost notifications."""
    if not settings().azure_servicebus_namespace:
        return
    from azure.servicebus import ServiceBusClient, ServiceBusMessage
    with ServiceBusClient(settings().azure_servicebus_namespace, credential()) as client:
        with client.get_queue_sender(settings().azure_servicebus_queue) as sender:
            sender.send_messages(ServiceBusMessage(job_id, message_id=job_id))
