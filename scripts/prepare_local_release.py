"""Create allowlisted release build/QA contexts; never run inference or publish."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from scripts.check_linux_container import prepare as prepare_qa, SECRET


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(root, output):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output == root or any(output.is_relative_to(root/f) for f in ('src','config','scripts','tests','data','.github')):
        raise ValueError('Release artifacts must be outside source folders')
    if output.exists():raise FileExistsError('Release output must be new')
    paths=[Path(n) for n in ('Dockerfile.pilot','.dockerignore','requirements.txt','constraints-pilot.txt','scripts/pilot_backup.py')]
    for folder in ('src','config'):
        paths.extend(p.relative_to(root) for p in (root/folder).rglob('*') if p.is_file()
            and (p.suffix in {'.py','.html','.co','.json','.yml','.yaml'} or p.name=='Modelfile') and '__pycache__' not in p.parts)
    payloads={}
    for rel in sorted(set(paths)):
        if any(word in rel.name.lower() for word in ('token','secret','credential','private','identities')):
            raise ValueError('Private configuration filename rejected')
        source=root/rel
        if source.is_symlink() or not source.resolve().is_relative_to(root):raise ValueError('External source link rejected')
        data=source.read_bytes()
        if SECRET.search(data):raise ValueError('Credential-shaped build content rejected')
        payloads[rel.as_posix()]=data
    hashes={n:hashlib.sha256(v).hexdigest() for n,v in payloads.items()}
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
    dirty=bool(subprocess.run(['git','status','--porcelain'],cwd=root,capture_output=True,text=True,check=True).stdout.strip())
    output.mkdir(parents=True,exist_ok=False)
    for name,data in payloads.items():
        target=output/'build'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    qa=prepare_qa(root,output/'qa')
    record={'format':'ami-release-source-v1','head':head,'dirty':dirty,'source_sha256':fingerprint,
        'revision_label':f'{head}-source-{fingerprint[:16]}' if dirty else head,'build_files':hashes,
        'qa_context_sha256':qa['context_sha256'],'dependency_files':{p.name:sha(p) for p in root.glob('requirements*.txt')}|
            {p.name:sha(p) for p in root.glob('constraints*.txt')},
        'exclusions':['credentials','owner databases','reports','virtual environments','Git metadata','external datasets'],
        'qualification':'Source capture only; no clean install, tests, inference, remote CI or deployment implied'}
    (output/'source.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return record


def build(root, output, image):
    record=prepare(root,output);output=Path(output).resolve()
    command=['docker','build','--progress=plain','-f',str(output/'build/Dockerfile.pilot'),
        '--build-arg','SOURCE_REVISION='+record['revision_label'],'-t',image,str(output/'build')]
    with (output/'docker-build.txt').open('w',encoding='utf-8') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        (output/'build-status.json').write_text(json.dumps({'status':'failed','exit_code':result.returncode}))
        raise RuntimeError('Build failed; inspect docker-build.txt')
    inspection=subprocess.run(['docker','image','inspect',image],capture_output=True,text=True,check=True).stdout
    (output/'image-inspect.json').write_text(inspection,encoding='utf-8')
    program="import importlib.metadata as m,json,os,subprocess,sys; p=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True); print(json.dumps({'uid':os.getuid(),'packages':{d.metadata['Name'].lower():d.version for d in m.distributions()},'pip_check_exit':p.returncode,'pip_check':p.stdout}));sys.exit(p.returncode)"
    result=subprocess.run(['docker','run','--rm','--network','none','--read-only',image,'python','-c',program],capture_output=True,text=True,check=True)
    (output/'dependencies.json').write_text(result.stdout,encoding='utf-8')
    installed=json.loads(result.stdout)
    if installed['uid']!=10001:raise ValueError('Image is not non-root')
    (output/'build-status.json').write_text(json.dumps({'status':'passed','image_id':json.loads(inspection)[0]['Id'],
        'revision_label':record['revision_label'],'fresh_install_claimed':False,'cache_evidence':'Inspect docker-build.txt; cached and executed install layers reported separately'},indent=2),encoding='utf-8')
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--image');args=parser.parse_args(argv)
    result=build(Path.cwd(),args.output,args.image) if args.image else prepare(Path.cwd(),args.output)
    print(json.dumps({'source_sha256':result['source_sha256'],'revision_label':result['revision_label'],'dirty':result['dirty']}))
    return 0


if __name__=='__main__':raise SystemExit(main())
