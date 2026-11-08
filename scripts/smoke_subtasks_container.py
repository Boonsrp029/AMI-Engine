"""No-inference image smoke of the explicit-plan concurrent runner."""
import argparse,json,subprocess,uuid
from pathlib import Path


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--image',required=True);p.add_argument('--qa',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(argv)
    a.output.mkdir(parents=True,exist_ok=False);volume='ami-f-smoke-'+uuid.uuid4().hex
    report={'image':a.image,'status':'started','actual_provider_calls':0,'synthetic_only':True}
    def docker(*args):return subprocess.run(['docker',*args],capture_output=True,text=True,check=True,timeout=180).stdout
    try:
        docker('volume','create',volume)
        command=['run','--rm','--network','none','--read-only','--tmpfs','/tmp','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--mount',f'type=volume,source={volume},target=/state','--mount',f'type=bind,source={a.qa.resolve()},target=/qa,readonly',
            '--env','PYTHONPATH=/app:/qa/tests/fixtures/workers','--workdir','/app',a.image,'python','/qa/tests/fixtures/release/concurrent_smoke.py']
        for phase,extra in [('execution',[]),('restart',['--verify'])]:
            text=docker(*(command+extra));(a.output/(phase+'.txt')).write_text(text,encoding='utf-8');report[phase]=json.loads(text)
        report['status']='passed'
    except Exception as e:
        report.update(status='failed',error_type=type(e).__name__)
        if isinstance(e,subprocess.CalledProcessError):
            (a.output/'failure-stdout.txt').write_text(e.stdout or '',encoding='utf-8')
            (a.output/'failure-stderr.txt').write_text(e.stderr or '',encoding='utf-8')
        raise
    finally:
        cleanup=subprocess.run(['docker','volume','rm',volume],capture_output=True,text=True)
        report['disposable_volume_cleanup']=cleanup.returncode==0
        (a.output/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return 0


if __name__=='__main__':raise SystemExit(main())
