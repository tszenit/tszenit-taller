

(function(){
"use strict";
var P="{{PFX}}";
var LS={get:function(k,d){try{var v=localStorage.getItem(P+k);return v?JSON.parse(v):d}catch(e){return d}},set:function(k,v){try{localStorage.setItem(P+k,JSON.stringify(v))}catch(e){}}};
function $(s,r){return (r||document).querySelector(s)}
function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))}
var TABS=$$('.tile').map(function(t){return t.dataset.tab});
function showTab(id,scroll){
  if(TABS.indexOf(id)<0)id=TABS[0];
  $$('.tile').forEach(function(t){t.setAttribute('aria-selected',t.dataset.tab===id?'true':'false')});
  TABS.forEach(function(t){document.getElementById(t).hidden=(t!==id)});
  LS.set('tab',id);
  if(scroll){var bar=$('.bar');var y=document.getElementById(id).getBoundingClientRect().top+window.scrollY-bar.offsetHeight-12;window.scrollTo({top:Math.max(0,y)})}
}
$$('.tile').forEach(function(t){t.addEventListener('click',function(){showTab(t.dataset.tab,true);t.scrollIntoView({block:'nearest',inline:'nearest'})})});
$$('[data-go]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();showTab(a.dataset.go,true)})});
showTab(LS.get('tab',TABS[0]),false);
var dom=LS.get('dom',{}),subs=$$('[data-sub]');
function refreshDom(){var done=0;
  TABS.forEach(function(t){var list=$$('#'+t+' [data-sub]');var d=list.filter(function(s){return dom[s.dataset.sub]}).length;var bar=$('.tile[data-tab="'+t+'"] .pg span');if(bar)bar.style.width=(list.length?Math.round(d/list.length*100):0)+'%'});
  subs.forEach(function(s){var b=$('.dom',s);var on=!!dom[s.dataset.sub];if(on)done++;b.setAttribute('aria-pressed',on?'true':'false');b.textContent=on?'Dominado ✓':'Marcar como dominado'});
  $('#stDom').textContent=done+'/'+subs.length}
subs.forEach(function(s){var h=$('.subh',s);if(h&&!$('.dom',h)){var b=document.createElement('button');b.className='dom';b.type='button';h.appendChild(b)}
  $('.dom',s).addEventListener('click',function(){dom[s.dataset.sub]=!dom[s.dataset.sub];LS.set('dom',dom);refreshDom()})});
refreshDom();
$$('[data-tool]').forEach(function(el){var f=window.TZT&&window.TZT[el.dataset.tool];if(f){try{f(el)}catch(e){el.innerHTML='<p class="err">No se pudo cargar esta herramienta.</p>';if(window.console)console.error(e)}}});
})();
