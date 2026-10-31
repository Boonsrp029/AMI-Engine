"""Existing-index checks use fixed metadata and never authenticate to Databricks."""
import importlib
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def existing(monkeypatch):
    for key in ('DATABRICKS_VECTOR_SEARCH_ENDPOINT', 'DATABRICKS_SOURCE_TABLE',
                'DATABRICKS_VECTOR_SEARCH_INDEX', 'DATABRICKS_VECTOR_SEARCH_PRIMARY_KEY',
                'DATABRICKS_EMBEDDING_SOURCE_COLUMN', 'DATABRICKS_EMBEDDING_MODEL_ENDPOINT'):
        monkeypatch.delenv(key, raising=False)
    with patch('src.utils.env.load_project_environment'):
        module = importlib.import_module('src.indexers.vector_search_sync')
    sdk = MagicMock()
    sdk.endpoint_exists.return_value = True
    sdk.index_exists.return_value = True
    with patch.object(module, 'AISearchClient', return_value=sdk):
        manager = module.MarketVectorSearchIndexer()
    metadata = {'name': manager.index_name, 'index_type': 'DELTA_SYNC', 'primary_key': manager.primary_key,
        'delta_sync_index_spec': {'source_table': manager.source_table, 'pipeline_type': 'TRIGGERED',
            'embedding_source_columns': [{'name': manager.embedding_column,
                'embedding_model_endpoint_name': manager.embedding_model}]}}
    index = sdk.get_index.return_value
    index.describe.return_value = metadata
    return manager, sdk, index, metadata


def test_matching_existing_contract_described_before_sync(existing):
    manager, sdk, index, _ = existing
    manager.sync_index('triggered')
    assert [call[0] for call in index.method_calls] == ['describe', 'sync', 'wait_until_ready']
    sdk.create_delta_sync_index.assert_not_called()


@pytest.mark.parametrize('damage', ['name', 'index_type', 'primary_key', 'source_table',
    'pipeline_type', 'column_name', 'model_endpoint', 'missing_spec', 'missing_columns',
    'extra_columns', 'malformed_column', 'malformed_metadata'])
def test_incompatible_or_incomplete_metadata_never_syncs_or_recreates(existing, damage):
    manager, sdk, index, metadata = existing
    spec = metadata['delta_sync_index_spec']
    private = 'synthetic-private-value'
    if damage in {'name', 'index_type', 'primary_key'}:
        metadata[damage] = private
    elif damage in {'source_table', 'pipeline_type'}:
        spec[damage] = private
    elif damage == 'column_name':
        spec['embedding_source_columns'][0]['name'] = private
    elif damage == 'model_endpoint':
        spec['embedding_source_columns'][0]['embedding_model_endpoint_name'] = private
    elif damage == 'missing_spec':
        metadata.pop('delta_sync_index_spec')
    elif damage == 'missing_columns':
        spec.pop('embedding_source_columns')
    elif damage == 'extra_columns':
        spec['embedding_source_columns'].append({})
    elif damage == 'malformed_column':
        spec['embedding_source_columns'] = [private]
    else:
        index.describe.return_value = [private]
    with pytest.raises(ValueError) as error:
        manager.sync_index()
    assert private not in str(error.value)
    index.sync.assert_not_called()
    index.wait_until_ready.assert_not_called()
    sdk.create_delta_sync_index.assert_not_called()


def test_describe_failure_propagates_without_sync_or_repair(existing):
    manager, sdk, index, _ = existing
    failure = RuntimeError('synthetic metadata access denied')
    index.describe.side_effect = failure
    with pytest.raises(RuntimeError) as error:
        manager.sync_index()
    assert error.value is failure
    index.sync.assert_not_called()
    sdk.create_delta_sync_index.assert_not_called()
