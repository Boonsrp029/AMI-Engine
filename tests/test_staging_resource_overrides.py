"""Offline resource configuration; mocked SDK, no workspace authentication."""
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


@pytest.mark.parametrize('configured,argument,expected', [
    (None, {}, 'feed_id'),
    (None, {'primary_key': 'constructor_id'}, 'constructor_id'),
    ('job_id', {}, 'job_id'),
    ('job_id', {'primary_key': 'constructor_id'}, 'job_id'),
])
def test_index_creation_uses_resolved_primary_key(monkeypatch, configured, argument, expected):
    if configured is None:
        monkeypatch.delenv('DATABRICKS_VECTOR_SEARCH_PRIMARY_KEY', raising=False)
    else:
        monkeypatch.setenv('DATABRICKS_VECTOR_SEARCH_PRIMARY_KEY', configured)
    with patch('src.utils.env.load_project_environment'):
        module = importlib.import_module('src.indexers.vector_search_sync')
    sdk = MagicMock()
    sdk.endpoint_exists.return_value = True
    sdk.index_exists.return_value = False
    with patch.object(module, 'AISearchClient', return_value=sdk):
        indexer = module.MarketVectorSearchIndexer(**argument)
        indexer.sync_index()
    assert sdk.create_delta_sync_index.call_args.kwargs['primary_key'] == expected
    sdk.create_delta_sync_index.assert_called_once()
    sdk.get_index.assert_not_called()
    sdk.create_delta_sync_index.return_value.wait_until_ready.assert_called_once()


def test_bundle_host_is_explicit_and_no_inert_override_is_advertised():
    config = yaml.safe_load(Path('databricks.yml').read_text(encoding='utf-8'))
    assert 'workspace_host' not in config['variables']
    workspace = config['targets']['dev']['workspace']
    assert workspace['host'] == 'https://dbc-567e5110-5578.cloud.databricks.com'
    assert '${var.' not in workspace['host']
    assert workspace['auth_type'] == 'databricks-cli'
