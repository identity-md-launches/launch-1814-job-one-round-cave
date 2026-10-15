"""One-time pigment transfer from installed image generation output, in memory.

The two input hashes prevent accidental reapplication. Only generated leaf
pigment is added to vacant stone; all other ancestral pixels remain exact.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from image_bytes import read_png, png

ANCESTOR = 'd04584a1de60bc2a7ac085bf04d4fe0ccf0a9835da79e5eb8f19e047590be00d'
GENERATED = '85d214a9de60a162171443d4582aa61738d5e1c65967a9c115738d481d883956'
PROMPT = ('A single small prehistoric cave-painted fallen leaf, symbol of passing time, '
          'centered on plain pale warm ochre stone. Leaf occupies central half of square, '
          'pointed oval, one curved charcoal stem and a few uneven charcoal veins, dry '
          'red ochre pigment rubbed thin with worn gaps and bare stone showing through. '
          'Handmade burnt-stick and thumb painting like Lascaux. Flat earth pigment only, '
          'not realistic leaf or 3D. No other objects, no hands, no letters, numbers, words, '
          'signature, logos, watermark, border or frame. This generated pigment will be '
          'composited onto a preexisting cave wall; keep the leaf isolated, all outer '
          'corners clear unmarked pale stone.')


def main():
    wall = Path('artifacts/line-1/wall.png')
    named = Path('artifacts/line-1/wall-v17.png')
    old, draft = wall.read_bytes(), named.read_bytes()
    assert hashlib.sha256(old).hexdigest() == ANCESTOR
    assert hashlib.sha256(draft).hexdigest() == GENERATED
    w, h, original = read_png(old)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (1254, 1254)
    assert (gw, gh) == (1254, 1254)
    result = bytearray(original)
    # Area sample only red ochre/charcoal pixels from the generated leaf. Its
    # generated background is discarded, not used to replace ancestral stone.
    for dy in range(90):
        for dx in range(52):
            colors = []
            for sy in range(130 + dy*11, 130 + (dy+1)*11):
                for sx in range(340 + dx*11, 340 + (dx+1)*11):
                    i = (sy*gw+sx)*3
                    r, g, b = generated[i:i+3]
                    if g < .62*r or max(r, g, b) < 80:
                        colors.append((r, g, b))
            if not colors:
                continue
            coverage = len(colors)/121
            alpha = .78*coverage
            i = ((880+dy)*w+450+dx)*3
            for c in range(3):
                pigment = sum(color[c] for color in colors)/len(colors)
                # Darken only: keep the original stone and crack modulation.
                result[i+c] = min(original[i+c], round(
                    original[i+c]*(1-alpha) + pigment*alpha))
    changed = [(i//3 % w, i//3//w) for i in range(0, len(original), 3)
               if original[i:i+3] != result[i:i+3]]
    assert 500 < len(changed) < 4680
    assert all(450 <= x < 502 and 880 <= y < 970 for x, y in changed)
    final = png(w, h, result)
    wall.write_bytes(final)
    named.write_bytes(final)
    thumb = subprocess.run([
        '/opt/tools/bin/ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-i', str(wall), '-vf', 'scale=512:512:flags=area', '-frames:v', '1',
        '-q:v', '4', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'],
        check=True, capture_output=True, env={}).stdout
    assert thumb[:2] == b'\xff\xd8' and thumb[-2:] == b'\xff\xd9'
    assert len(thumb) < 100000
    Path('dist/line-1/37.jpg').write_bytes(thumb)
    digest = hashlib.sha256(final).hexdigest()
    record = {
        'name': 'The Fallen Leaf',
        'image': 'https://api.imd.fun/artifacts/' + digest,
        'attributes': [{'trait_type': k, 'value': v} for k, v in (
            ('Cave', 'Water'), ('Wall', 'Line 1'), ('Number', 37),
            ('Left behind', 'Snapshot capture age'),
            ('Meaning', 'A fallen leaf reminds Pepe to measure the age of what he carries.'),
            ('One thing', 'portable live Ethereum JSON-RPC snapshots'))]}
    path = Path('dist/line-1/37.json')
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2) + '\n')
    review = {
        'record': 37, 'ancestor_sha256': ANCESTOR, 'output_sha256': digest,
        'wall': {'paths': [str(wall), str(named)], 'width': w, 'height': h,
                 'format': 'PNG', 'mode': 'RGB', 'bytes': len(final)},
        'thumbnail': {'path': 'dist/line-1/37.jpg', 'width': 512, 'height': 512,
                      'format': 'JPEG', 'bytes': len(thumb)},
        'generation': {'tool': 'mcp__image__generate_image', 'prompt': PROMPT,
                       'draft_sha256': GENERATED, 'draft_retained': False},
        'changed_pixels': len(changed), 'unchanged_pixels': w*h-len(changed),
        'changed_bounds_inclusive': [min(x for x,y in changed), min(y for x,y in changed),
                                     max(x for x,y in changed), max(y for x,y in changed)],
        'preservation': 'Only generated pigment on vacant lower-left rock was added. '
                        'All other pixels are ancestral; no older painting was touched.',
        'visual_review': 'Pending final inspection.', 'unmet_visual_requirements': []}
    Path('line-1/wall-review-37.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
