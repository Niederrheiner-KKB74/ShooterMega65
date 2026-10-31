// Deterministic pixel-source converter. Node.js 18+, no dependencies.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {deflateSync} from 'node:zlib';
import crypto from 'node:crypto';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const src = JSON.parse(fs.readFileSync(path.join(root,'assets/aircraft/source/aircraft.json'),'utf8'));
const out = path.join(root,'assets/aircraft/generated');
fs.mkdirSync(out,{recursive:true});
function crc(b) { let c=0xffffffff; for(const v of b){c^=v;for(let k=0;k<8;k++) c=(c>>>1)^((c&1)?0xedb88320:0);}return (c^0xffffffff)>>>0; }
function chunk(type,data){const t=Buffer.from(type),n=Buffer.alloc(4),c=Buffer.alloc(4);n.writeUInt32BE(data.length);c.writeUInt32BE(crc(Buffer.concat([t,data])));return Buffer.concat([n,t,data,c]);}
function png(w,h,pixels){const ih=Buffer.alloc(13);ih.writeUInt32BE(w);ih.writeUInt32BE(h,4);ih[8]=8;ih[9]=6;const raw=[];for(let y=0;y<h;y++){raw.push(0);for(let x=0;x<w;x++){const i=pixels[y*w+x];raw.push(...src.palette[i],i===0?0:255);}}return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ih),chunk('IDAT',deflateSync(Buffer.from(raw))),chunk('IEND',Buffer.alloc(0))]);}
if(src.palette.length!==16 || src.palette.some(c=>c.length!==3 || c.some(v=>!Number.isInteger(v)||v<0||v>255))) throw Error('Invalid 16-entry RGB palette');
const manifest={schema:1,provenance:src.provenance,hardwareTested:false,transparentIndex:0,palette:src.palette,sprites:[]};
const sheet=Array(144*32).fill(0);
for(const [si,s] of src.sprites.entries()){
 if(!/^[a-z0-9_-]+$/.test(s.id)||![16,24].includes(s.width)||s.height!==s.width||s.rows.length!==s.height||s.rows.some(r=>r.length!==s.width||!/^[.1-9a-f]+$/.test(r))) throw Error('Invalid sprite '+s.id);
 const pixels=s.rows.join('').split('').map(c=>c==='.'?0:parseInt(c,16));
 fs.writeFileSync(path.join(out,s.id+'.indices.bin'),Buffer.from(pixels));
 fs.writeFileSync(path.join(out,s.id+'.png'),png(s.width,s.height,pixels));
 const entry={id:s.id,width:s.width,height:s.height,facing:s.facing,formats:{}};
 for(const [mode,tw] of [['fcm',8],['ncm',16]]){
  const cols=Math.ceil(s.width/tw),rows=Math.ceil(s.height/8),data=[];
  for(let ty=0;ty<rows;ty++)for(let tx=0;tx<cols;tx++)for(let y=0;y<8;y++)for(let x=0;x<tw;x+=mode==='ncm'?2:1){
   const at=(dx)=>{const px=tx*tw+x+dx,py=ty*8+y;return px<s.width&&py<s.height?pixels[py*s.width+px]:0;};
   data.push(mode==='ncm'?at(0)|(at(1)<<4):at(0));
  }
  const bytes=Buffer.from(data);const file=s.id+'.'+mode+'.bin';fs.writeFileSync(path.join(out,file),bytes);
  entry.formats[mode]={file,tileWidth:tw,tileHeight:8,columns:cols,rows,storedWidth:cols*tw,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
 }
 manifest.sprites.push(entry);
 for(let y=0;y<s.height;y++)for(let x=0;x<s.width;x++)sheet[(y+4)*144+si*28+x+2]=pixels[y*s.width+x];
}
fs.writeFileSync(path.join(out,'sheet.png'),png(144,32,sheet));
const scale=6,large=[];for(let y=0;y<32*scale;y++)for(let x=0;x<144*scale;x++)large.push(sheet[Math.floor(y/scale)*144+Math.floor(x/scale)]);
fs.writeFileSync(path.join(out,'preview-6x.png'),png(144*scale,32*scale,large));
fs.writeFileSync(path.join(out,'palette.rgb'),Buffer.from(src.palette.flat()));
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log('Built '+manifest.sprites.length+' sprites (FCM/NCM, PNG, palette, manifest)');
