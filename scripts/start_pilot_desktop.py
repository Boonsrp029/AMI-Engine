"""Start the local analyst app from an existing image, without running evaluation."""
import argparse
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default=os.getenv('AMI_PILOT_IMAGE'),
        help='Locally built analyst image; no registry pull or build is performed')
    parser.add_argument('--corpus', type=Path,
        default=ROOT / 'data/external/market_sources/prepared/market_chunks.json')
    parser.add_argument('--check', action='store_true', help='Validate paths, image and Compose without starting')
    args = parser.parse_args(argv)
    if not args.image:
        parser.error('Set --image to a locally built analyst image')
    # Desktop backends may create missing bind directories even when Compose
    # requests create_host_path:false. Reject them before any Docker call.
    corpus = args.corpus.resolve()
    if not corpus.is_file():
        parser.error('--corpus must be an existing JSON file, not a directory or missing path')
    try:
        json.loads(corpus.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        parser.error(f'Cannot read corpus JSON ({type(exc).__name__})')
    image = subprocess.run(['docker', 'image', 'inspect', args.image],
        check=True, capture_output=True, text=True)
    config = json.loads(image.stdout)[0]['Config']
    command = config.get('Cmd') or []
    if not any(command[i:i+2] == ['-m', 'src.pilot.launch'] for i in range(len(command))):
        parser.error('Image does not use the analyst launcher; main.py is the evaluation CLI')
    env = {**os.environ, 'AMI_PILOT_IMAGE': args.image, 'AMI_PILOT_CORPUS_FILE': str(corpus)}
    compose = ['docker', 'compose', '--project-name', 'ami-engine-desktop',
        '-f', str(ROOT / 'compose.desktop.yml')]
    subprocess.run([*compose, 'config', '--quiet'], cwd=ROOT, env=env, check=True)
    if args.check:
        print('Local image, corpus and Compose configuration validated; nothing started.')
        return 0
    subprocess.run([*compose, 'up', '-d', '--no-build', '--pull', 'never', 'market-agent'],
        cwd=ROOT, env=env, check=True)
    print('Analyst app started on the configured localhost port (default http://127.0.0.1:8000).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
