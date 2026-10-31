// Independent decode checks, including transparent NCM padding and nibble order.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const src=JSON.parse(fs.readFileSync(path.join(root,'assets/aircraft/source/aircraft.json')));
const dir=path.join(root,'assets/aircraft/generated');
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
assert.equal(src.sprites.length,5);
assert.equal(manifest.hardwareTested,false);
for(const s of src.sprites){
 const expected=Buffer.from(s.rows.join('').split('').map(c=>c==='.'?0:parseInt(c,16)));
 assert(!expected.includes(15),'NCM index 15 is colour-RAM special value');
 assert(expected.some(v=>v!==0));
 assert.deepEqual(fs.readFileSync(path.join(dir,s.id+'.indices.bin')),expected);
 for(const [mode,tw] of [['fcm',8],['ncm',16]]){
  const bytes=fs.readFileSync(path.join(dir,s.id+'.'+mode+'.bin'));
  const cols=Math.ceil(s.width/tw),rows=Math.ceil(s.height/8);
  assert.equal(bytes.length,cols*rows*64);
  for(let y=0;y<rows*8;y++)for(let x=0;x<cols*tw;x++){
   const tile=Math.floor(y/8)*cols+Math.floor(x/tw);
   const b=bytes[tile*64+(y%8)*8+Math.floor((x%tw)/(mode==='ncm'?2:1))];
   const v=mode==='ncm'?((b>>>((x%2)*4))&15):b;
   assert.equal(v,x<s.width&&y<s.height?expected[y*s.width+x]:0,`${s.id} ${mode} (${x},${y})`);
  }
 }
}
// Known asymmetric pair: left colour 3, right colour 10 => byte $A3.
assert.equal(0xa3&15,3);assert.equal(0xa3>>>4,10);
console.log('PASS: all 5 sources decode pixel-exactly from FCM and NCM; padding is zero.');
