"""Transfer only generated trail pigment onto vacant ancestral rock."""
import hashlib
import json
from pathlib import Path

from image_bytes import jpeg, png, read_png, resize


def main():
    folder = Path('artifacts/line-4')
    ancestor = (folder/'wall.png').read_bytes()
    draft = (folder/'wall-v17.png').read_bytes()
    old_sha = '6fdf7a75644d3d4a0865ac532945f497bbfb3dc19cf7231b44705135a1e809ee'
    assert hashlib.sha256(ancestor).hexdigest() == old_sha
    w, h, old = read_png(ancestor)
    dw, dh, generated = read_png(draft)
    assert (w, h, dw, dh) == (1254, 1254, 1254, 1254)
    final = bytearray(old)
    centers = [(1127, 811, 19), (1114, 853, 15), (1087, 888, 14)]
    for y in range(791, 906):
        for x in range(1069, 1148):
            j = (y*w+x)*3
            r,g,b = generated[j:j+3]
            pebble = any((x-cx)**2+(y-cy)**2 < radius**2 for cx,cy,radius in centers)
            red = pebble and 55 < r < 200 and r > 1.5*g and r-g > 30
            # Thin connecting stroke; retain only dark generated pixels.
            line_x = 1114 + (853-y)*.65 if y > 853 else 1127 + (811-y)*.31
            line = 813 < y < 887 and abs(x-line_x) < 2.6 and max(r,g,b) < 82
            if not (red or line):
                continue
            tx,ty = x-75,y+90
            i = (ty*w+tx)*3
            original = old[i:i+3]
            if sum(original) < 75:  # protect original deep rock cracks
                continue
            if red:
                # Blend the editor's pigment with the target's original texture.
                target = bytes(round(a*.30+p*.70) for a,p in zip(original,(r,g,b)))
            else:
                target = bytes(round(a*.60) for a in original)
            final[i:i+3] = target
    changes = []
    for i in range(0,len(old),3):
        if old[i:i+3] != final[i:i+3]:
            y,x = divmod(i//3,w)
            assert 994 <= x < 1073 and 881 <= y < 996 and sum(old[i:i+3]) >= 75
            changes.append((x,y))
    assert 300 < len(changes) < 3500
    wall = png(w,h,final)
    sha = hashlib.sha256(wall).hexdigest()
    preview = jpeg(512,512,resize(w,h,final),52)
    assert len(preview) < 100000
    for name in ('wall.png','wall-v17.png'):
        (folder/name).write_bytes(wall)
    Path('dist/line-4/37.jpg').write_bytes(preview)
    record = {'name':'The Witness Trail','image':'https://api.imd.fun/artifacts/'+sha,
              'attributes':[
                  {'trait_type':'Cave','value':'Water'},
                  {'trait_type':'Wall','value':'Line 4'},
                  {'trait_type':'Number','value':37},
                  {'trait_type':'Left behind','value':'offline EIP-712 witness path'},
                  {'trait_type':'Meaning','value':'Pepe follows three ochre stones from a field through its enclosing hashes.'},
                  {'trait_type':'One thing','value':'offline EIP-712 typed-data digest checking'}]}
    Path('dist/line-4/37.json').write_text(json.dumps(record,indent=2)+'\n')
    review = {
        'wall': {'paths':['artifacts/line-4/wall.png','artifacts/line-4/wall-v17.png'],
                 'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(wall),'sha256':sha},
        'preview':{'path':'dist/line-4/37.jpg','width':512,'height':512,'format':'JPEG',
                   'bytes':len(preview),'sha256':hashlib.sha256(preview).hexdigest()},
        'ancestorSha256':old_sha,'generatedDraftSha256':hashlib.sha256(draft).hexdigest(),
        'imageTool':'installed image edit_image; explicit workspace PNG output',
        'promptSummary':'Add a small ascending trail of three red ochre pebbles on vacant rock. Preserve cave, all ancestors, Pepe and five-digit hands. No text or new hands.',
        'changedPixels':len(changes),'unchangedPixels':w*h-len(changes),
        'additionBoundsExclusive':[min(x for x,y in changes),min(y for x,y in changes),max(x for x,y in changes)+1,max(y for x,y in changes)+1],
        'preservation':'Only generated pigment selected from draft and transferred to vacant lower-right stone. All other pixels and deep cracks remain exactly ancestral.',
        'visualReview':'Pending final PNG and JPEG inspection.',
        'unmetVisualRequirements':[],
        'limitations':['Local visual review is not independent certification.',
                       'Small mark is subtle in the JPEG preview.',
                       'The draft changed surrounding stone; only selected trail pigment was retained.']}
    Path('line-4/wall-review-37.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
