"""Release context boundaries; synthetic directories and no Docker/network."""
import subprocess
from pathlib import Path
import pytest
from scripts.prepare_local_release import prepare


def tree(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    for name in ['Dockerfile.pilot','.dockerignore','requirements.txt','constraints-pilot.txt','scripts/pilot_backup.py','src/x.py','config/ollama/Modelfile']:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# synthetic\n')
    for name in ['.env','owner.sqlite3','reports/private.json','.venv/site.py','data/external/private.json']:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('excluded private marker')
    # Supply a HEAD without a commit operation: the test mocks revision discovery.
    return root


def test_build_context_excludes_private_material_and_keeps_modelfile(tmp_path,monkeypatch):
    root=tree(tmp_path)
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:subprocess.CompletedProcess(a[0],0,stdout='synthetic-head\n'))
    out=tmp_path/'release';r=prepare(root,out)
    assert 'config/ollama/Modelfile' in r['build_files']
    assert not any(n.startswith(('reports/','.venv/','data/')) for n in r['build_files'])
    assert not (out/'build/.env').exists() and not (out/'qa/data/external').exists()
    assert (out/'build/src/x.py').read_bytes()==(root/'src/x.py').read_bytes()
    with pytest.raises(FileExistsError):prepare(root,out)


def test_credential_shaped_code_rejected_before_output_creation(tmp_path,monkeypatch):
    root=tree(tmp_path);(root/'src/x.py').write_text('dapi'+'a'*32)
    with pytest.raises(ValueError,match='Credential'):prepare(root,tmp_path/'release')
    assert not (tmp_path/'release').exists()


def test_source_output_directory_rejected(tmp_path):
    root=tree(tmp_path)
    with pytest.raises(ValueError,match='outside source'):
        prepare(root,root/'src/release')
    assert not (root/'src/release').exists()


def test_private_config_filename_rejected_without_reading_it(tmp_path):
    root=tree(tmp_path);(root/'config/private-tokens.json').write_text('private')
    with pytest.raises(ValueError,match='Private configuration'):
        prepare(root,tmp_path/'release')
    assert not (tmp_path/'release').exists()
