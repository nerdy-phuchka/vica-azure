from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_mode: str = 'local'
    database_url: str = 'sqlite:///./data/vca.db'
    local_storage_path: str = './data/files'
    dev_auth_enabled: bool = False
    dev_auth_token: str = ''
    dev_proxy_secret: str = ''
    entra_tenant_id: str = ''
    entra_audience: str = ''
    azure_storage_account_url: str = ''
    azure_storage_container: str = 'documents'
    azure_document_endpoint: str = ''
    azure_openai_endpoint: str = ''
    azure_openai_deployment: str = ''
    azure_search_endpoint: str = ''
    azure_search_index: str = 'vca-evidence'
    azure_servicebus_namespace: str = ''
    azure_servicebus_queue: str = 'document-jobs'
    azure_client_id: str = ''
    los_callback_url: str = ''
    los_callback_secret: str = ''
    max_upload_mb: int = 50
    max_document_pages: int = 200
    max_ai_characters: int = 80000
    policy_file: str = '../02_Configuration/policy.pending.json'
    scanner_mode: str = 'disabled-local'
    clamav_host: str = ''
    clamav_port: int = 3310
    field_review_required: bool = True
    run_migrations: bool = True

    def validate_runtime(self):
        if self.app_mode not in ('local', 'azure'):
            raise RuntimeError('APP_MODE must be local or azure')
        if self.app_mode == 'azure':
            required = [self.entra_tenant_id, self.entra_audience,
                        self.azure_storage_account_url, self.azure_document_endpoint,
                        self.azure_openai_endpoint, self.azure_openai_deployment]
            if self.dev_auth_enabled or not all(required):
                raise RuntimeError('Azure mode requires Entra, storage and AI configuration; dev auth is forbidden')
            if self.database_url.startswith('sqlite'):
                raise RuntimeError('Azure mode requires PostgreSQL')
            if self.scanner_mode != 'clamav' or not self.clamav_host:
                raise RuntimeError('Azure mode requires a configured upload scanner')
            if self.los_callback_url and not self.los_callback_url.startswith('https://'):
                raise RuntimeError('Azure LOS callbacks require HTTPS')
        if self.dev_auth_enabled and len(self.dev_auth_token) < 24:
            raise RuntimeError('Local development token must have at least 24 characters')
        Path(self.local_storage_path).mkdir(parents=True, exist_ok=True)


@lru_cache
def settings():
    return Settings()
