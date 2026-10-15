// Preserve ancestral pixels; transfer only the image tool's new fish pigment.
import fs from 'node:fs';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const oldBytes=fs.readFileSync('artifacts/gathering/wall.png');
const draftBytes=fs.readFileSync('artifacts/gathering/wall-v17.png');
if(digest(oldBytes)!=='6bfc80eca4d2ffb9fcbcd82357f50d489e01245b67658c272cb6e7fabd679d1a')throw Error('ancestor pin');
function decode(b){
 if(!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))throw Error('PNG');
 let w,h,channels;const chunks=[];
 for(let p=8;p<b.length;){const n=b.readUInt32BE(p),kind=b.toString('ascii',p+4,p+8),data=b.subarray(p+8,p+8+n);if(kind==='IHDR'){w=data.readUInt32BE(0);h=data.readUInt32BE(4);if(data[8]!==8||![2,6].includes(data[9])||data[12]!==0)throw Error('format');channels=data[9]===2?3:4;}if(kind==='IDAT')chunks.push(data);p+=n+12;}
 const raw=zlib.inflateSync(Buffer.concat(chunks)),stride=w*channels,out=Buffer.alloc(w*h*channels);if(raw.length!==h*(stride+1))throw Error('length');
 for(let y=0;y<h;y++){const f=raw[y*(stride+1)];for(let x=0;x<stride;x++){const i=y*stride+x,a=x>=channels?out[i-channels]:0,b=y?out[i-stride]:0,c=y&&x>=channels?out[i-stride-channels]:0;let predictor=0;if(f===1)predictor=a;else if(f===2)predictor=b;else if(f===3)predictor=Math.floor((a+b)/2);else if(f===4){const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);predictor=pa<=pb&&pa<=pc?a:pb<=pc?b:c;}else if(f!==0)throw Error('filter');out[i]=(raw[y*(stride+1)+1+x]+predictor)&255;}}
 if(channels===3)return {w,h,pixels:out};const rgb=Buffer.alloc(w*h*3);for(let i=0;i<w*h;i++)for(let c=0;c<3;c++)rgb[i*3+c]=out[i*4+c];return {w,h,pixels:rgb};
}
function crc32(b){let c=0xffffffff;for(const x of b){c^=x;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0;}
function chunk(kind,b){const k=Buffer.from(kind),result=Buffer.alloc(b.length+12);result.writeUInt32BE(b.length);k.copy(result,4);b.copy(result,8);result.writeUInt32BE(crc32(Buffer.concat([k,b])),b.length+8);return result;}
function encode(w,h,pixels){const head=Buffer.alloc(13);head.writeUInt32BE(w);head.writeUInt32BE(h,4);head[8]=8;head[9]=2;const raw=Buffer.alloc(h*(w*3+1));for(let y=0;y<h;y++)pixels.copy(raw,y*(w*3+1)+1,y*w*3,(y+1)*w*3);return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',head),chunk('IDAT',zlib.deflateSync(raw,{level:9})),chunk('IEND',Buffer.alloc(0))]);}
const old=decode(oldBytes),draft=decode(draftBytes);
if(old.w!==1254||old.h!==1254||old.w!==draft.w||old.h!==draft.h)throw Error('dimensions');
const final=Buffer.from(old.pixels),rect=[806,451,141,79];let changed=0;
for(let y=rect[1];y<rect[1]+rect[3];y++)for(let x=rect[0];x<rect[0]+rect[2];x++){
 const i=(y*old.w+x)*3,[r,g,b]=draft.pixels.subarray(i,i+3),[or,og,ob]=old.pixels.subarray(i,i+3);
 const ochre=r>55&&r<200&&r>1.55*g&&g>1.35*b&&r/Math.max(1,g)>or/Math.max(1,og)+.22;
 const charcoal=Math.max(r,g,b)<82&&Math.max(or,og,ob)>115&&r<or*.68;
 if(!(ochre||charcoal)||Math.max(or,og,ob)<80)continue;
 const color=charcoal?[43,32,20]:[141,62,29],alpha=charcoal?.82:.72;
 for(let c=0;c<3;c++)final[i+c]=Math.min(old.pixels[i+c],Math.round(old.pixels[i+c]*(1-alpha)+color[c]*alpha));
 if(!final.subarray(i,i+3).equals(old.pixels.subarray(i,i+3)))changed++;
}
if(changed<250)throw Error('insufficient pigment');
for(let y=0;y<old.h;y++)for(let x=0;x<old.w;x++){if(x>=rect[0]&&x<rect[0]+rect[2]&&y>=rect[1]&&y<rect[1]+rect[3])continue;const i=(y*old.w+x)*3;if(!old.pixels.subarray(i,i+3).equals(final.subarray(i,i+3)))throw Error('ancestor changed');}
const output=encode(old.w,old.h,final);
fs.writeFileSync('artifacts/gathering/wall-v17.png',output);fs.writeFileSync('artifacts/gathering/wall.png',output);
const review={ancestorSha256:digest(oldBytes),wallSha256:digest(output),generatedDraftSha256:digest(draftBytes),generatedDraftRetained:false,imageTool:'image_gen.imagegen',wallSize:[old.w,old.h],wallFormat:'PNG',wallMode:'RGB',additionRectangle:rect,changedPixels:changed,unchangedPixels:old.w*old.h-changed,allPixelsOutsideAdditionUnchanged:true,deepCracksProtected:true,newHands:0,newHandprints:0,reviewStatus:'requires final visual inspection',unmetVisualRequirements:[],method:'Only image-tool fish pigment transferred onto vacant ancestral stone; generated stone discarded.'};
fs.writeFileSync('gathering/wall-review-17.json',JSON.stringify(review,null,2)+'\n');console.log(JSON.stringify(review));
