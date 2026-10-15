"""Check this round's declared delivery bytes and unchanged ancestral source."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from image_bytes import read_png


def main():
    report = json.loads(Path('line-4/wall-review-37.json').read_text())
    a = Path('artifacts/line-4/wall.png').read_bytes()
    b = Path('artifacts/line-4/wall-v17.png').read_bytes()
    assert a == b
    w,h,pixels = read_png(a)
    assert (w,h) == (1254,1254)
    sha = hashlib.sha256(a).hexdigest()
    assert sha == report['wall']['sha256']
    assert report['wall']['format'] == 'PNG'
    assert report['unmetVisualRequirements'] == []
    assert 'Pending' not in report['visualReview']
    preview = Path('dist/line-4/37.jpg').read_bytes()
    assert preview[:2] == b'\xff\xd8' and preview[-2:] == b'\xff\xd9'
    assert len(preview) < 100000
    assert hashlib.sha256(preview).hexdigest() == report['preview']['sha256']
    offset, dimensions = 2, None
    while offset < len(preview):
        assert preview[offset] == 255
        marker = preview[offset+1]
        length = int.from_bytes(preview[offset+2:offset+4], 'big')
        if marker == 192:
            bits,jh,jw,channels = struct.unpack('>BHHB',preview[offset+4:offset+10])
            assert (bits,channels) == (8,3)
            dimensions = (jw,jh)
            break
        offset += 2+length
    assert dimensions == (512,512)
    record = json.loads(Path('dist/line-4/37.json').read_text())
    assert set(record) == {'name','image','attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/'+sha
    attrs = record['attributes']
    assert len(attrs) == 6 and all(set(x) == {'trait_type','value'} for x in attrs)
    assert [x['trait_type'] for x in attrs] == ['Cave','Wall','Number','Left behind','Meaning','One thing']
    assert [x['value'] for x in attrs[:3]] == ['Water','Line 4',37]
    assert type(attrs[2]['value']) is int
    records = list(Path('dist/line-4').glob('[0-9][0-9].json'))
    assert len(records) == 37
    # Read only repository baseline objects, never machine configuration.
    changed = subprocess.check_output(['git','diff','--name-only'],text=True).splitlines()
    assert changed == ['line-4/USED.md'], changed
    baseline_goal = subprocess.check_output(['git','show','HEAD:line-4/GOAL.md'])
    assert Path('line-4/GOAL.md').read_bytes() == baseline_goal
    for entry in json.loads(Path('line-4/tools/witness-path/provenance.json').read_text()):
        data = (Path('line-4/tools/witness-path')/entry['copy']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        assert data == Path(entry['source']).read_bytes()
    untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines()
    for name in untracked:
        assert name.startswith(('line-4/','dist/line-4/','artifacts/line-4/')), name
        if not name.startswith('artifacts/'):
            assert Path(name).stat().st_size <= 100000, name
    assert report['changedPixels']+report['unchangedPixels'] == w*h
    result = {'passed':True,'wallWidth':w,'wallHeight':h,'wallFormat':'PNG',
              'previewWidth':512,'previewHeight':512,'previewFormat':'JPEG',
              'previewBytes':len(preview),'wallSha256':sha,'recordNumber':37,
              'goalUnchanged':True,'olderTrackedWorkUnchanged':True,
              'vendorHashesMatch':True,'unmetVisualRequirements':[],
              'scope':'Local byte and structure checks; visual inspection is recorded separately.'}
    Path('line-4/delivery-check-37.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
