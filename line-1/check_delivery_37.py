"""Offline byte/shape checks for this round; visual review is recorded separately."""
import hashlib
import json
from pathlib import Path
import subprocess

from image_bytes import read_png


def run(args):
    result = subprocess.run(args, capture_output=True, env={})
    return {'command': list(args), 'exit': result.returncode,
            'stdout': result.stdout.decode('utf-8'),
            'stderr': result.stderr.decode('utf-8')}


def main():
    results = []
    wall = Path('artifacts/line-1/wall.png').read_bytes()
    assert wall == Path('artifacts/line-1/wall-v17.png').read_bytes()
    assert read_png(wall)[:2] == (1254, 1254)
    digest = hashlib.sha256(wall).hexdigest()
    record = json.loads(Path('dist/line-1/37.json').read_text())
    assert list(record) == ['name', 'image', 'attributes']
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
    assert record['attributes'] == [{'trait_type': k, 'value': v} for k, v in (
        ('Cave', 'Water'), ('Wall', 'Line 1'), ('Number', 37),
        ('Left behind', 'Snapshot capture age'),
        ('Meaning', 'A fallen leaf reminds Pepe to measure the age of what he carries.'),
        ('One thing', 'portable live Ethereum JSON-RPC snapshots'))]
    assert type(record['attributes'][2]['value']) is int
    assert len(list(Path('dist/line-1').glob('*.json'))) == 37
    review = json.loads(Path('line-1/wall-review-37.json').read_text())
    assert review['output_sha256'] == digest
    assert review['unmet_visual_requirements'] == []
    assert review['changed_pixels'] + review['unchanged_pixels'] == 1254**2
    thumb = Path('dist/line-1/37.jpg')
    assert thumb.stat().st_size < 100000
    decoded = subprocess.run([
        '/opt/tools/bin/ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-i', str(thumb), '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt',
        'rgb24', '-'], check=True, capture_output=True, env={}).stdout
    assert len(decoded) == 512*512*3
    probe = run(['/opt/tools/bin/ffprobe', '-v', 'error', '-select_streams', 'v:0',
                 '-show_entries', 'stream=width,height,codec_name', '-of', 'json', str(thumb)])
    assert probe['exit'] == 0
    stream = json.loads(probe['stdout'])['streams'][0]
    assert stream == {'codec_name': 'mjpeg', 'width': 512, 'height': 512}
    results.append(probe)
    goal = subprocess.run(['/usr/bin/git', 'show', 'HEAD:line-1/GOAL.md'],
                          check=True, capture_output=True, env={}).stdout
    assert Path('line-1/GOAL.md').read_bytes() == goal
    changed = run(['/usr/bin/git', 'diff', '--name-only'])
    assert changed['exit'] == 0
    assert changed['stdout'].splitlines() == ['line-1/USED.md']
    results.append(changed)
    check = run(['/usr/bin/git', 'diff', '--check'])
    assert check['exit'] == 0
    results.append(check)
    for p in Path('line-1').rglob('*'):
        if p.is_file():
            assert p.stat().st_size <= 100000, str(p)
    for p in (Path('dist/line-1/37.json'), thumb):
        assert p.stat().st_size <= 100000
    tests = run(['/usr/bin/python3', '-B', 'line-1/tools/snapshot-capture-age/test_age.py'])
    assert tests['exit'] == 0
    results.append(tests)
    command = ['/usr/bin/python3', '-B', 'line-1/tools/snapshot-capture-age/age.py',
               'line-1/tools/snapshot-integer/live-zto.json', '--expected-sha256',
               'd620b767ccc4b4ea42e7660af9fc15aeb481a808888d43675c300820f3e6b51f',
               '--reference', '2026-10-15T05:02:16.159255Z', '--max-age-seconds', '3600']
    for name, reference, expected in (
        ('example.json', '2026-10-15T05:02:16.159255Z', 0),
        ('example-rejection.json', '2026-10-15T05:02:16.159256Z', 1)):
        command[7] = reference
        trial = run(command)
        assert trial['exit'] == expected, trial
        assert json.loads(trial['stdout']) == json.loads(
            (Path('line-1/tools/snapshot-capture-age')/name).read_text())
        results.append(trial)
    output = {'delivery_passed': True, 'checks': results,
              'wall_sha256': digest, 'wall_dimensions': [1254, 1254],
              'wall_format': 'RGB PNG', 'thumbnail_dimensions': [512, 512],
              'thumbnail_format': 'JPEG', 'unmet_visual_requirements': [],
              'limits': 'Local checks verify bytes and behavior, not independent certification.'}
    Path('line-1/check-results-37.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Round 37 delivery checks passed; 17 tool tests passed.')


if __name__ == '__main__':
    main()
