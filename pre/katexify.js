const katex=require('/home/claude/zenit/tools/node_modules/katex');
let s=require('fs').readFileSync(0,'utf8');let bad=0;
function r(t,d){try{return katex.renderToString(t,{output:'mathml',displayMode:d,throwOnError:true,strict:false})}catch(e){bad++;process.stderr.write('KATEX ERR: '+t+' :: '+e.message.slice(0,120)+'\n');return '<code>'+t+'</code>'}}
s=s.replace(/⟪([\s\S]+?)⟫/g,(_,t)=>r(t,true)).replace(/⟦([\s\S]+?)⟧/g,(_,t)=>r(t,false));
s=s.replace(/<mi mathvariant="double-struck">R<\/mi>/g,'<mi mathvariant="normal">ℝ</mi>');const FN='(?:ln|log|sin|cos|tan|sen|cot|sec|csc|exp|arcsen|arccos|arctan)';
s=s.replace(new RegExp('(</mi>|</mn>|</msup>|</msub>|</mo>(?=<mi[^>]*>'+FN+'</mi>))(<mi(?: mathvariant="normal")?>'+FN+'</mi>)','g'),function(_,a,b){return a.indexOf('mo')>=0?a+b:a+'<mspace width="0.17em"></mspace>'+b});
s=s.replace(/(<msub><mrow><mi(?: mathvariant="normal")?>[a-z]+<\/mi><mo>⁡<\/mo><\/mrow>[\s\S]*?<\/msub>)(?!<mo)/g,'$1<mspace width="0.17em"></mspace>');
s=s.replace(/<mo>⁡<\/mo>(?!<\/mrow>|<mo)/g,'<mo>⁡</mo><mspace width="0.17em"></mspace>');
process.stdout.write(s);if(bad)process.exitCode=0;
