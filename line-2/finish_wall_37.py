"""Transfer only generated flat pigment into vacant stone; preserve ancestral pixels."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

base=Path('artifacts/line-2/wall.png')
output=Path('artifacts/line-2/wall-v17.png')
ancestor,draft=base.read_bytes(),output.read_bytes()
assert hashlib.sha256(ancestor).hexdigest()=='5a99d18ba9a9fdd8b342f16dee3668956268e69b4dd7de7901e8127bf268f5ec'
w,h,old=read_png(ancestor)
dw,dh,generated=read_png(draft)
assert (w,h)==(1254,1254)
assert (dw,dh)==(1024,1024)
x0,y0,width,height=950,280,135,85
sx0,sy0,sw,sh=90,138,845,695
final=bytearray(old)
changed=0
for y in range(y0,y0+height):
    for x in range(x0,x0+width):
        i=(y*w+x)*3
        rock=old[i:i+3]
        sx=sx0+(x-x0)*sw//width
        sy=sy0+(y-y0)*sh//height
        j=(sy*dw+sx)*3
        r,g,b=generated[j:j+3]
        # Preserve dark ancestral cracks and leave worn gaps in the added pigment.
        if max(rock)<55 or (x*19+y*31)%17<2:
            continue
        radius=((sx-511)/418)**2+((sy-484)/340)**2
        charcoal=max(r,g,b)<112 and .60<radius<1.09
        ochre=(r>1.45*g and 38<g<138 and b<93 and
               (((sx-390)/112)**2+((sy-470)/134)**2<1 or
                ((sx-657)/118)**2+((sy-470)/138)**2<1))
        if charcoal or ochre:
            pigment=(40,29,20) if charcoal else (151,65,29)
            alpha=.66 if charcoal else .58
            for c in range(3):
                final[i+c]=round(rock[c]*(1-alpha)+pigment[c]*alpha)
            changed+=final[i:i+3]!=old[i:i+3]
assert 500<changed<width*height
for y in range(h):
    for x in range(w):
        i=(y*w+x)*3
        if final[i:i+3]!=old[i:i+3]:
            assert x0<=x<x0+width and y0<=y<y0+height
            assert max(old[i:i+3])>=55
encoded=png(w,h,final)
base.write_bytes(encoded)
output.write_bytes(encoded)
preview=jpeg(512,512,resize(w,h,final),52)
assert len(preview)<100000
Path('dist/line-2/37.jpg').write_bytes(preview)
review={'number':37,'ancestor_sha256':hashlib.sha256(ancestor).hexdigest(),
        'sha256':hashlib.sha256(encoded).hexdigest(),
        'wall':{'paths':[str(base),str(output)],'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(encoded)},
        'preview':{'path':'dist/line-2/37.jpg','width':512,'height':512,'format':'JPEG','bytes':len(preview)},
        'addition_region':{'x':x0,'y':y0,'width':width,'height':height},
        'changed_pixels':changed,'unchanged_pixels':w*h-changed,
        'outside_region_pixel_identical':True,'dark_cracks_preserved':True,
        'generation_tool':'mcp__image__generate_image',
        'generation_model':'black-forest-labs/flux-schnell',
        'draft_sha256':hashlib.sha256(draft).hexdigest(),'generated_dimensions':[dw,dh],
        'draft_retained':False,
        'generation_prompt':'An isolated small prehistoric cave painting motif on warm light ochre rough stone: exactly two oval red ochre pebbles, side by side, encircled together by one uneven charcoal black oval loop, with a short charcoal connecting stroke between the pebbles. Center motif occupies middle 65 percent of square image. Earth pigments, Lascaux burnt stick and thumb marks, worn and irregular, bare rock visible through pigment, torchlight. No letters, numbers, symbols, logos, hands, people, border, watermark, photograph or 3D render. This is an insert painting to transfer onto an existing cave wall, representing two components that form one key.',
        'compositing':'Only flat charcoal and ochre pigment sampled from generated motif; generated stone, shading and highlights discarded.',
        'visual_review':'pending inspection',
        'unmet_visual_requirements':['Inherited hands have unresolved digit detail; exact five-digit count cannot be certified. No hands or handprints added.']}
Path('line-2/wall-review-37.json').write_text(json.dumps(review,indent=2)+'\n')
record={'name':'Two Stones, One Key','image':'https://api.imd.fun/artifacts/'+review['sha256'],
        'attributes':[{'trait_type':k,'value':v} for k,v in [
            ('Cave','Water'),('Wall','Line 2'),('Number',37),
            ('Left behind','Offline JSON Lines composite key checker'),
            ('Meaning','Pepe binds two pebbles in one loop so only the whole pair can repeat.'),
            ('One thing','offline JSON structural contract checking')]]}
Path('dist/line-2/37.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(review,indent=2))
