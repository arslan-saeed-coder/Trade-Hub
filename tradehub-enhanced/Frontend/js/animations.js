// Lightweight UI helpers for the single-owner store.
document.addEventListener('DOMContentLoaded',()=>{
  const btn=document.getElementById('back-to-top');
  window.addEventListener('scroll',()=>{const p=document.getElementById('scroll-progress'); if(p){const h=document.documentElement.scrollHeight-window.innerHeight; p.style.width=(h?window.scrollY/h*100:0)+'%';} if(btn)btn.style.display=window.scrollY>300?'block':'none';});
  btn?.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
});
