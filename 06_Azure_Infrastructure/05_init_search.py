"""Run inside worker container (or VNet-connected host) after RBAC propagation."""
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SearchFieldDataType
from app.storage import credential
from app.config import settings

client=SearchIndexClient(settings().azure_search_endpoint,credential())
index=SearchIndex(name=settings().azure_search_index,fields=[
    SimpleField(name='id',type=SearchFieldDataType.String,key=True),
    SimpleField(name='case_id',type=SearchFieldDataType.String,filterable=True),
    SimpleField(name='document_id',type=SearchFieldDataType.String,filterable=True),
    SimpleField(name='page',type=SearchFieldDataType.Int32),
    SearchableField(name='content',type=SearchFieldDataType.String,analyzer_name='standard.lucene')])
client.create_or_update_index(index)
print('Evidence index initialised. Case filter is applied by the authorised API.')
