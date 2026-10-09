import hashlib
import http.server
import json
import os
import re
import socketserver
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from html import unescape

PORT = 8000

# Trabajos recientes (sección Portafolio). Agrega o quita los que quieras.
# "titulo": el nombre que se muestra debajo de la miniatura.
# Miniatura: el servidor la trae sola del video y la guarda en la carpeta miniaturas/
# (para descargarla otra vez, borra su archivo de esa carpeta). Si alguna no sale,
# guarda tu propia imagen junto a este archivo como trabajo1.jpg, trabajo2.jpg... (o .png / .webp).
# Opcional: pip install yt-dlp  (sirve de respaldo y suele traer también las de Facebook).
TRABAJOS = [
    {"url": "https://www.tiktok.com/@ybuenoahoraque/video/7665168707013971220", "plataforma": "TikTok", "titulo": "What if, Clark Backrooms"},
    {"url": "https://www.facebook.com/reel/2271158373453274", "plataforma": "Facebook", "titulo": "Publicidad departamento Colors"},
    {"url": "https://www.tiktok.com/@bufete.juridico.ga/video/7692513319885819142", "plataforma": "TikTok", "titulo": "Bufete Jurídico Galindo"},
]

HTML = '<!doctype html>\n<!--\n  Una sola página, CSS puro (sin frameworks). Cambios visuales y de estructura:\n  - Dos columnas: menú a la izquierda y panel de contenido a la derecha; en celular se apilan.\n  - Modo oscuro negro grisáceo con dorado; modo claro blanco y gris azulado. Sigue la configuración del sistema.\n  - Letra Krona One para el nombre, Sora para títulos y Montserrat para el texto; bordes suaves y espacios amplios.\n  - Transición suave entre secciones y esqueleto de carga si no hay internet.\n  - Fondo plano: negro grisáceo en modo oscuro y gris claro en modo claro; solo el brillo del mouse lo cambia.\n  - Modo ligero automático para celulares de poca memoria.\n-->\n<html lang="es" class="cargando">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<title>P-Frames, publicidad</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<script>var gfFail=!navigator.onLine,gfDone=new Promise(function(r){window.gfOk=r});\n(function(){var c=navigator.connection;if((navigator.deviceMemory&&navigator.deviceMemory<=4)||(c&&c.saveData)||(matchMedia(\'(pointer:coarse)\').matches&&innerWidth<=820))document.documentElement.classList.add(\'lite\')})();\n(function(){try{localStorage.removeItem(\'tema\')}catch(e){}\ndocument.documentElement.dataset.theme=matchMedia(\'(prefers-color-scheme:light)\').matches?\'light\':\'dark\';})();</script>\n<link id="gf" rel="stylesheet" media="print" onload="this.media=\'all\';gfOk()" onerror="gfFail=true;gfOk()" href="https://fonts.googleapis.com/css2?family=Sora:wght@400..700&family=Montserrat:wght@300..700&display=swap">\n<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@400..700&family=Montserrat:wght@300..700&display=swap"><style>.skel{display:none}html.cargando body>.shell{visibility:visible}</style></noscript>\n<style>\n:root{\n  --a:#161617; --b:#0c0c0d; --c:#141414;\n  --ink:#eceae6; --ink-soft:rgba(236,234,230,.72); --line:rgba(255,255,255,.13);\n  --paper:#0c0c0d; --bg0:#161618; --card:#0f0f11;\n  --gold:#d4af37; --gold-l:#f0d78a; --gold-d:#4d3b0c; --r:6px; --r-l:10px; --fondo:#161618; color-scheme:dark;\n  --display:\'Sora\',\'Montserrat\',system-ui,sans-serif;\n  --sans:\'Montserrat\',system-ui,-apple-system,\'Segoe UI\',Roboto,sans-serif;\n  box-sizing:border-box;\n  padding-top:env(safe-area-inset-top,0px);\n  padding-bottom:env(safe-area-inset-bottom,0px);\n}\n:root[data-theme="light"]{\n  --a:#ffffff; --b:#f1f4f8; --c:#e8edf3;\n  --ink:#1a2029; --ink-soft:rgba(26,32,41,.7); --line:rgba(60,80,110,.16);\n  --paper:#ffffff; --bg0:#e9ecf0; --card:#ffffff;\n  --gold:#5a6a80; --gold-l:#a3b2c6; --gold-d:#364255; --fondo:#e9ecf0; color-scheme:light;\n}\nhtml{scroll-padding-top:env(safe-area-inset-top,0px)}\n*,*::before,*::after{box-sizing:border-box}\nbody{margin:0;min-height:100vh;background:var(--bg0);color:var(--ink);font-family:var(--sans);font-size:1rem;line-height:1.5}\n.bg{position:fixed;inset:0;z-index:-1;background:var(--fondo)}\n\n.shell{display:grid;grid-template-columns:minmax(220px,260px) 1fr;gap:clamp(24px,4vw,64px);align-items:start;\n  max-width:1440px;margin:0 auto;min-height:100vh;padding:clamp(24px,5vh,56px) clamp(18px,4vw,48px)}\n.side{display:flex;flex-direction:column;gap:28px;position:sticky;top:clamp(24px,5vh,56px)}\n.brand{display:flex;align-items:center;gap:10px;padding-bottom:20px;border-bottom:1px solid var(--line);font-family:var(--display);font-weight:700;font-size:1.35rem;letter-spacing:-.02em}\nnav{display:flex;flex-direction:column;align-items:flex-start;gap:8px}\nbutton{font:inherit;color:inherit;cursor:pointer}\nnav button{background:none;border:0;border-radius:var(--r);padding:10px 16px;margin-left:-16px;\n  font-family:var(--display);font-weight:500;font-size:1.3rem;letter-spacing:-.02em;color:var(--ink-soft);\n  transform-origin:left center;transition:transform .28s cubic-bezier(.2,.9,.3,1.2),color .2s}\nnav button:focus-visible{transform:scale(1.06);color:var(--ink)}\nnav button[aria-current="page"]{background:none;color:var(--ink);box-shadow:inset 0 0 0 1.5px var(--gold)}\n:focus-visible{outline:2px solid var(--gold);outline-offset:3px}\n.stage{position:relative;align-self:start;min-width:0}\n.panel{min-height:min(560px,80vh);display:flex;flex-direction:column;justify-content:flex-start;\n  background:var(--card);border:1px solid var(--line);border-radius:var(--r);\n  padding:clamp(28px,5vw,64px);backdrop-filter:none}\n@keyframes levita{50%{translate:0 -4px}}\n@keyframes levita-panel{50%{translate:0 -6px}}\n.panel{position:relative}\nnav button{animation:levita 5s ease-in-out infinite}\nnav button:nth-child(2){animation-delay:-1.7s}\nnav button:nth-child(3){animation-delay:-3.4s}\n.panel{animation:levita-panel 6.5s ease-in-out infinite}\n@media (max-width:820px){\n  .shell{grid-template-columns:1fr}\n  .side{gap:18px;justify-content:flex-start}\n  nav{flex-direction:row;flex-wrap:wrap}\n  nav button{margin-left:0;font-size:1.1rem}\n  nav button:focus-visible{transform:scale(1.06)}\n  @media (hover:hover){nav button:hover{transform:scale(1.06)}}\n  .panel{min-height:380px}\n}\nsection[hidden]{display:none}\nh1,h2{font-family:var(--display);font-weight:600;letter-spacing:-.035em;margin:0}\nh1{font-size:clamp(2.3rem,5.6vw,4.4rem);line-height:1.04;max-width:14ch}\nh2{font-size:clamp(2rem,4.6vw,3.2rem);line-height:1.08}\n.lead{max-width:46ch;font-size:clamp(1.05rem,2.3vw,1.3rem);line-height:1.55;color:var(--ink-soft);margin:22px 0 0}\n.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:32px}\n.btn{border:1px solid var(--line);border-radius:var(--r);display:inline-flex;align-items:center;justify-content:center;min-height:50px;padding:13px 24px;font-weight:600;background:none}\n.btn.main{background:none}\n.btn.alt{background:none}\n.btn.cta{border:0;min-height:54px;padding:15px 30px;font-size:1rem;color:#0c0c0d;background:var(--gold)}\n@media (hover:hover){.btn:hover{transform:translateY(-2px)}}\n\n.work{list-style:none;margin:32px 0 0;padding:0;border-top:1px solid var(--line)}\n.work li{display:grid;grid-template-columns:56px 1fr auto;align-items:center;gap:6px 20px;padding:20px 0;border-bottom:1px solid var(--line)}\n.sw{width:48px;height:48px;background:linear-gradient(135deg,var(--gold-l),var(--gold-d))}\n.work b{font-family:var(--display);font-weight:500;font-size:clamp(1.3rem,3.2vw,1.9rem);letter-spacing:-.01em}\n.work span.m{color:var(--ink-soft);font-size:.95rem;text-align:right}\n@media (max-width:560px){.work span.m{grid-column:2;text-align:left}}\n\n.lines{margin-top:32px;border-top:1px solid var(--line)}\n.line{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:4px 24px;padding:22px 0;\n  border-bottom:1px solid var(--line);color:inherit;text-decoration:none}\n.line small{font-size:.9rem;color:var(--ink-soft)}\n.line strong{font-family:var(--display);font-weight:500;font-size:clamp(1.5rem,4.6vw,2.6rem);letter-spacing:-.015em;\n  text-decoration:underline;text-decoration-color:transparent;text-underline-offset:6px;text-decoration-thickness:2px}\n.line:hover strong{text-decoration-color:var(--gold)}\n\n/* Transición suave */\nsection{animation:entra .38s cubic-bezier(.2,.8,.3,1) backwards}\nsection.out{animation:sale .16s ease forwards}\n@keyframes entra{from{opacity:0;transform:translateY(16px)}}\n@keyframes sale{to{opacity:0;transform:translateY(10px)}}\n\n/* Fondo que cambia de color por donde pasa el mouse */\n.glow{position:fixed;left:-260px;top:-260px;width:520px;height:520px;z-index:-1;pointer-events:none;opacity:0;transition:opacity .5s;\n  background:radial-gradient(circle closest-side,hsl(43 85% 55% / .12),transparent);will-change:transform}\n.glow.on{opacity:1}\n\n/* Esqueleto de carga */\nhtml.cargando body>.shell{visibility:hidden;animation:ver 0s 6s forwards}\n@keyframes ver{to{visibility:visible}}\n.skel{position:fixed;inset:0;z-index:90;overflow:hidden;transition:opacity .4s;animation:skel-fuera .4s 6s forwards}\n.skel.fuera{opacity:0;pointer-events:none}\n@keyframes skel-fuera{to{opacity:0;visibility:hidden}}\n.sk{display:block;border-radius:var(--r);\n  background:linear-gradient(90deg,var(--line) 20%,rgba(255,255,255,.12) 50%,var(--line) 80%);\n  background-size:200% 100%;animation:shimmer 1.3s linear infinite}\n@keyframes shimmer{from{background-position:100% 0}to{background-position:-100% 0}}\n.sk.pill{width:150px;height:46px;border-radius:var(--r)}\n.skel .panel .sk{margin-top:16px}\n.skel .panel .sk:first-child{margin-top:0}\n\n/* Celular */\n@supports (min-height:100svh){body,.shell{min-height:100svh}}\n@media (max-width:820px){.stage{align-self:start}}\n@media (max-width:560px){\n  .shell{padding:20px 16px 32px;gap:20px}\n  .panel{padding:22px 18px;border-radius:var(--r)}\n  .lead{margin-top:16px}\n  .actions{margin-top:24px}\n  .btn{padding:12px 20px}\n  .work li{padding:16px 0}\n  .line{padding:18px 0}\n  .line strong{font-size:1.15rem;overflow-wrap:anywhere}\n  .sk.pill{width:104px;height:42px}\n}\n\n/* Diseño enérgico */\n\n.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}\n.chips span{display:flex;align-items:center;gap:8px;padding:5px 12px;border:1px solid var(--line);border-radius:var(--r);font-weight:500;font-size:.88rem}\n.chips span::before{content:\'\';width:6px;height:6px;background:var(--gold)}\n\n/* Carrusel antes / después */\n@property --p{syntax:\'<percentage>\';inherits:true;initial-value:50%}\n.ba{position:relative;margin-top:56px;padding-top:32px;border-top:1px solid var(--line)}\n.ba-head{display:flex;align-items:center;flex-wrap:wrap;gap:10px}\n.ba-head b{font-family:var(--display);font-size:1.25rem;letter-spacing:-.02em;margin-right:auto}\n.ba-sub{margin:6px 0 16px;color:var(--ink-soft);font-size:.95rem}\n.ba-nav{display:flex;gap:8px}\n.ba-nav button{width:40px;height:40px;border:1px solid var(--line);background:none;font-size:1.4rem;line-height:1}\n@media (hover:hover){.ba-nav button:hover{color:var(--gold);border-color:var(--gold)}}\n.ba-view{overflow:hidden;border-radius:var(--r);touch-action:pan-y}\n.ba-track{display:flex;transition:transform .5s cubic-bezier(.2,.8,.3,1)}\n.ba-slide{flex:0 0 100%;display:grid;grid-template-columns:180px 1fr;align-items:center;gap:28px;padding:22px;border:1px solid var(--line);border-radius:var(--r)}\n.ph{--p:50%;position:relative;aspect-ratio:9/16;border-radius:var(--r);overflow:hidden;border:1px solid var(--line);cursor:ew-resize;user-select:none;touch-action:pan-y}\n@keyframes wipe-d{from{transform:translateX(14%)}to{transform:translateX(86%)}}\n@keyframes wipe-i{from{transform:translateX(-14%)}to{transform:translateX(-86%)}}\n.ph>div{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:flex-end;padding:12px 10px;text-align:center}\n.ph-a{background:linear-gradient(#4b4b53,#2a2a30);color:#a9a9b2;font-size:.62rem}\n/* La barrita se mueve con transform (lo hace la GPU) en vez de redibujar con clip-path */\n.ph>.ph-d{display:block;padding:0;overflow:hidden;will-change:transform;transform:translateX(var(--p));animation:wipe-d 5s ease-in-out infinite alternate}\n.ph-i{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:flex-end;padding:12px 10px;text-align:center;background:radial-gradient(circle at 72% 18%,rgba(255,255,255,.4),transparent 40%),linear-gradient(200deg,var(--gold-l),var(--gold) 50%,var(--gold-d));color:#fff;font-weight:800;font-size:1rem;line-height:1.1;text-transform:uppercase;text-shadow:0 2px 0 rgba(0,0,0,.35);will-change:transform;transform:translateX(calc(var(--p)*-1));animation:wipe-i 5s ease-in-out infinite alternate}\n.ph::after{content:\'\';position:absolute;inset:0 0 0 -1px;border-left:2px solid #fff;pointer-events:none;will-change:transform;transform:translateX(var(--p));animation:wipe-d 5s ease-in-out infinite alternate}\n.ph.man>.ph-d,.ph.man .ph-i,.ph.man::after{animation:none}\n.tg{position:absolute;top:8px;z-index:2;font-size:.62rem;font-weight:700;padding:2px 8px;border-radius:var(--r);background:rgba(0,0,0,.55);color:#fff}\n.tg.l{left:8px}.tg.r{right:8px}\n.ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;pointer-events:none}\n.ph img:not([src]){visibility:hidden}\n.ba-r{display:flex;flex-direction:column;justify-content:center;gap:12px;min-width:0}\n.ba-r h3{margin:0;font-family:var(--display);font-size:1.1rem;letter-spacing:-.02em}\n.ch{width:100%;height:auto;overflow:visible}\n.ln{fill:none;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1;stroke-dashoffset:1}\n.ln.a{stroke:#8d8d99}\n.ln.d{stroke:var(--gold)}\n.on .ln{animation:draw 1.2s .15s ease forwards}\n.on .ln.d{animation-delay:.5s}\n@keyframes draw{to{stroke-dashoffset:0}}\n.lg{display:flex;gap:16px;margin:0;font-size:.82rem;color:var(--ink-soft)}\n.lg i{display:inline-block;width:10px;height:10px;border-radius:var(--r);margin-right:6px;background:#8d8d99}\n.lg i+i,.lg i.d{background:var(--gold-l)}\n.mets{display:flex;flex-wrap:wrap;gap:8px 24px;padding-top:14px;border-top:1px solid var(--line)}\n.mets small{display:block;color:var(--ink-soft);font-size:.78rem}\n.mets b{font-family:var(--display);font-size:1.3rem;letter-spacing:-.02em}\n.mets i{font-style:normal;color:var(--ink-soft)}\n.mets em{font-style:normal;color:var(--gold-l)}\n.ba-dots{display:flex;justify-content:center;gap:8px;margin-top:14px}\n.ba-dots button{width:8px;height:8px;padding:0;border:0;border-radius:var(--r);background:var(--line);transition:width .3s}\n.ba-dots button[aria-current="true"]{width:26px;background:var(--gold)}\n@media (max-width:560px){\n  .ba-slide{grid-template-columns:1fr;padding:14px}\n  .ph{width:min(46%,150px);margin:0 auto}\n}\n\n.ba-slide:not(.on) .ph>.ph-d,.ba-slide:not(.on) .ph-i,.ba-slide:not(.on) .ph::after{animation-play-state:paused}\n\n/* Orden y respiro */\n.brand::before{content:\'\';width:8px;height:8px;flex:none;background:var(--gold)}\n.work:empty{display:none}\n@media (max-width:820px){\n  .shell{gap:20px}\n  .side{position:static;gap:16px}\n  .brand{padding-bottom:14px}\n  nav{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;width:100%}\n  nav button{margin-left:0;padding:12px 4px;font-size:.95rem;text-align:center}\n  nav button[aria-current="page"]{box-shadow:inset 0 0 0 1.5px var(--gold)}\n  .actions{display:grid;grid-template-columns:1fr 1fr}\n  .btn.cta{grid-column:1/-1}\n  .ba-head{display:grid;grid-template-columns:1fr auto;gap:8px 10px}\n  .ba-nav{grid-column:2;grid-row:1}\n}\n\n/* Modo claro (blanco y gris azulado) */\n.ch{color:var(--ink)}\n:root[data-theme="light"] .btn.cta{color:#fff}\n:root[data-theme="light"] .mets em{color:var(--gold-d)}\n:root[data-theme="light"] .ln.a{stroke:#b9c1cd}\n:root[data-theme="light"] .lg i:not(.d){background:#b9c1cd}\n:root[data-theme="light"] .glow{background:radial-gradient(circle closest-side,hsl(215 25% 55% / .16),transparent)}\n:root[data-theme="light"] .sk{background-image:linear-gradient(90deg,var(--line) 20%,rgba(255,255,255,.6) 50%,var(--line) 80%)}\n\n/* Bordes suaves */\n.panel,.ba-slide,.ba-view,nav button{border-radius:var(--r-l)}\n.ba-nav button,.sw,.tema{border-radius:var(--r)}\n.lg i,.chips span::before,.brand::before,.ba-dots button{border-radius:2px}\n\n/* Opciones en 3D (con mouse) */\nnav button{position:relative;transform-style:preserve-3d}\nnav button span{display:block;pointer-events:none;transition:transform .2s ease-out}\nnav button::before{content:\'\';position:absolute;inset:0;border-radius:inherit;pointer-events:none;opacity:0;transition:opacity .25s;\n  background:radial-gradient(circle at var(--gx,50%) var(--gy,50%),rgba(255,255,255,.16),transparent 60%)}\nnav button::after{content:\'\';position:absolute;inset:0;border-radius:inherit;pointer-events:none;z-index:-1;\n  background:rgba(0,0,0,.5);transform:translateZ(-18px);opacity:0;transition:opacity .25s}\n@media (hover:hover){\n  nav button{transform-origin:center;transition:transform .16s ease-out,color .2s,box-shadow .25s,background .25s}\n  nav button:hover{transform:perspective(700px) rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg)) scale(1.07);color:var(--ink);\n    background:linear-gradient(145deg,rgba(255,255,255,.08),rgba(255,255,255,.02));\n    box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 18px 30px -12px rgba(0,0,0,.65)}\n  nav button[aria-current="page"]:hover{box-shadow:inset 0 0 0 1.5px var(--gold),0 18px 30px -12px rgba(0,0,0,.65)}\n  nav button:hover span{transform:translateZ(26px)}\n  nav button:hover::before,nav button:hover::after{opacity:1}\n  :root[data-theme="light"] nav button:hover{background:linear-gradient(145deg,rgba(255,255,255,.95),rgba(255,255,255,.55));\n    box-shadow:inset 0 1px 0 #fff,0 18px 30px -12px rgba(30,45,70,.35)}\n  :root[data-theme="light"] nav button[aria-current="page"]:hover{box-shadow:inset 0 0 0 1.5px var(--gold),0 18px 30px -12px rgba(30,45,70,.35)}\n  :root[data-theme="light"] nav button::before{background:radial-gradient(circle at var(--gx,50%) var(--gy,50%),rgba(255,255,255,.7),transparent 60%)}\n  :root[data-theme="light"] nav button::after{background:rgba(30,45,70,.28)}\n}\n\n/* Disposición en computadora */\n@media (min-width:821px){\n  nav{align-items:stretch;gap:12px}\n  nav button{width:100%;text-align:left;margin-left:0;padding:16px 20px;border:1px solid var(--line);font-size:1.15rem}\n}\n@media (min-width:1360px){\n  #presentacion:not([hidden]){flex:1;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);grid-template-rows:1fr auto auto auto auto 1fr;column-gap:48px}\n  #presentacion>*{grid-column:1}\n  #presentacion>.chips{grid-row:2}\n  #presentacion>h1{grid-row:3}\n  #presentacion>.lead{grid-row:4}\n  #presentacion>.actions{grid-row:5}\n  #presentacion>.ba{grid-column:2;grid-row:1/span 6;align-self:center;margin-top:0;padding-top:0;border-top:0}\n  #presentacion h1{font-size:clamp(2.6rem,4vw,3.8rem)}\n  .ba-slide{grid-template-columns:1fr;gap:18px;padding:18px}\n  .ba-slide .ph{width:min(44%,150px);margin:0 auto}\n}\n\n/* Nombre en letra ancha y letras pequeñas ligeras */\nh1{font-family:\'Krona One\',var(--display);font-weight:400;letter-spacing:.01em;text-transform:uppercase;font-size:clamp(1.6rem,5.2vw,3.2rem);line-height:1.15;max-width:none}\n@media (min-width:1360px){#presentacion h1{font-size:clamp(1.8rem,2.9vw,2.9rem)}}\n.lead,.ba-sub{font-weight:300}\n:root[data-theme="light"] .lead,:root[data-theme="light"] .ba-sub{font-weight:400}\n\n/* Panel opaco: oscurece todo lo que queda detrás */\n.panel{box-shadow:0 30px 80px -10px rgba(0,0,0,.55)}\n:root[data-theme="light"] .panel{box-shadow:0 30px 80px -10px rgba(30,45,70,.18)}\n\n/* Modo ligero (celulares con poca memoria o ahorro de datos) */\n.lite .panel::before,.lite .btn.cta,.lite .panel,.lite nav button{animation:none}\n.lite .glow{display:none}\n.lite .ln.d{filter:none}\n\n/* Trabajos recientes */\n.trabajos{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:clamp(18px,2.4vw,32px);margin-top:32px}\n.trabajos:empty{display:none}\n.trab{display:flex;flex-direction:column;gap:14px;min-width:0;color:inherit;text-decoration:none}\n.mini{position:relative;aspect-ratio:1/1;overflow:hidden;border:1px solid var(--line);border-radius:var(--r-l);background:linear-gradient(135deg,var(--gold-l),var(--gold-d));transition:border-color .25s}\n.mini img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .5s cubic-bezier(.2,.8,.3,1)}\n.play{position:absolute;left:50%;top:50%;width:56px;height:56px;margin:-28px 0 0 -28px;border-radius:50%;background:rgba(0,0,0,.45);border:1px solid rgba(255,255,255,.4)}\n.play::before{content:\'\';position:absolute;left:50%;top:50%;margin:-9px 0 0 -6px;border-left:15px solid #fff;border-top:9px solid transparent;border-bottom:9px solid transparent}\n.tt{margin:0;font-family:var(--display);font-weight:600;font-size:clamp(1.05rem,1.5vw,1.3rem);letter-spacing:-.01em;line-height:1.2;text-transform:uppercase;\n  display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}\n.plat{display:flex;align-items:center;gap:10px;margin:auto 0 0;color:var(--ink-soft);font-size:.9rem}\n.plat::before{content:\'\';width:8px;height:8px;flex:none;border-radius:50%;background:#f5c518}\n@media (hover:hover){.trab:hover .mini{border-color:var(--gold)}.trab:hover .mini img{transform:scale(1.06)}}\n.trab:focus-visible{outline:none}\n.trab:focus-visible .mini{border-color:var(--gold);box-shadow:0 0 0 2px var(--gold)}\n@media (prefers-reduced-motion:reduce){.mini img{transition:none}.trab:hover .mini img{transform:none}}\n\n@media (prefers-reduced-motion:reduce){\n  .bg::before,.panel,.panel::before,nav button,.sk,.btn.cta,.ph,.ph>.ph-d,.ph-i,.ph::after{animation:none}\n  .ln{animation:none!important;stroke-dashoffset:0}\n  .btn:hover{transform:none}\n  nav button:hover,nav button:hover span{transform:none}\n}\n</style>\n<style id="fuente">@font-face{font-family:\'Krona One\';font-weight:400;font-display:block;src:url(data:font/woff2;base64,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) format(\'woff2\')}</style>\n</head>\n<body>\n<div class="bg" aria-hidden="true"></div>\n<div class="glow" aria-hidden="true"></div>\n\n<div class="skel" id="skel" aria-hidden="true">\n  <div class="shell">\n    <aside class="side">\n      <i class="sk" style="width:120px;height:26px"></i>\n      <nav><i class="sk pill"></i><i class="sk pill"></i><i class="sk pill"></i></nav>\n    </aside>\n    <div class="stage"><div class="panel">\n      <i class="sk" style="width:72%;height:56px"></i>\n      <i class="sk" style="width:100%;height:16px"></i>\n      <i class="sk" style="width:90%;height:16px"></i>\n      <i class="sk" style="width:55%;height:16px"></i>\n      <i class="sk" style="width:150px;height:48px;border-radius:var(--r);margin-top:28px"></i>\n    </div></div>\n  </div>\n</div>\n\n<div class="shell">\n<aside class="side">\n  <div class="brand">P-Frames</div>\n  <nav aria-label="Secciones">\n    <button data-go="presentacion" aria-current="page"><span>Inicio</span></button>\n    <button data-go="portafolio"><span>Portafolio</span></button>\n    <button data-go="contactos"><span>Contactos</span></button>\n  </nav>\n</aside>\n\n<div class="stage">\n<main class="panel">\n  <section id="presentacion">\n    <div class="chips"><span>TikTok</span><span>Reels</span><span>Shorts</span></div>\n    <h1>Fernando David.</h1>\n    <p class="lead">Director y Editor de vídeos, shorts, reels, tiktoks publicitarios o de entretenimiento, para que te quedes en la mente de tus clientes.</p>\n    <div class="actions">\n      <button class="btn cta" data-go="contactos">Quiero mi video</button>\n    </div>\n\n    <div class="ba" role="region" aria-roledescription="carrusel" aria-label="Antes y después">\n      <div class="ba-head">\n        <b>Antes y después</b>\n        <div class="ba-nav"><button type="button" aria-label="Anterior" data-ba="-1">&lsaquo;</button><button type="button" aria-label="Siguiente" data-ba="1">&rsaquo;</button></div>\n      </div>\n      <p class="ba-sub">Así cambia la retención: cuánta gente sigue viendo el video, segundo a segundo.</p>\n      <div class="ba-view" id="baView"><div class="ba-track" id="baTrack"></div></div>\n      <div class="ba-dots" id="baDots"></div>\n    </div>\n  </section>\n\n  <section id="portafolio" hidden>\n    <h2>Trabajos recientes</h2>\n    <div class="trabajos" id="work"></div>\n  </section>\n\n  <section id="contactos" hidden>\n    <h2>Hablemos.</h2>\n    <p class="lead">Cuéntame qué quieres promocionar, que idea tienes en mente y te respondo al instante.</p>\n    <div class="lines">\n      <a class="line" href="galindofernandodavid@gmail.com"><small>Correo</small><strong>galindofernandodavid@gmail.com</strong></a>\n      <a class="line" href="https://wa.me/59170000000" target="_blank" rel="noopener"><small>WhatsApp</small><strong>+591 69407202</strong></a>\n    </div>\n  </section>\n</main>\n\n</div>\n</div>\n\n<script>\n// Los trabajos se editan arriba, en la lista TRABAJOS del archivo .py\nconst works=__TRABAJOS__;\nfunction fm(i){if(i.dataset.alt&&!i.dataset.r){i.dataset.r=1;i.referrerPolicy=\'no-referrer\';i.src=i.dataset.alt;}else i.remove();}\ndocument.getElementById(\'work\').innerHTML=works.map((w,i)=>\n  `<a class="trab" href="${w.url}" target="_blank" rel="noopener"><span class="mini"><img src="/miniatura/${i}" alt="" draggable="false" decoding="async"${w.alt?` data-alt="${w.alt}"`:\'\'} onerror="fm(this)"><i class="play"></i></span><h3 class="tt"></h3><p class="plat">${w.plataforma}</p></a>`).join(\'\');\nworks.forEach((w,i)=>{\n  const el=document.querySelectorAll(\'#work .tt\')[i];\n  if(w.titulo){el.textContent=w.titulo;return;}\n  fetch(\'/titulo/\'+i).then(r=>r.ok?r.text():\'\').catch(()=>\'\').then(t=>{el.textContent=t||(\'Video de \'+w.plataforma);});\n});\n\nconst $=id=>document.getElementById(id);\nlet current=\'presentacion\',target=\'presentacion\',run=0;\n\nfunction mark(id){\n  document.querySelectorAll(\'nav button\').forEach(b=>{\n    if(b.dataset.go===id)b.setAttribute(\'aria-current\',\'page\');else b.removeAttribute(\'aria-current\');\n  });\n}\n\nfunction show(id){\n  document.querySelectorAll(\'main section\').forEach(s=>s.hidden=s.id!==id);\n  mark(id);\n  current=id;\n  window.scrollTo(0,0);\n}\n\nfunction go(id){\n  if(id===target)return;\n  target=id;\n  const my=++run;\n  mark(id);\n  const cur=document.querySelector(\'main section:not([hidden])\');\n  if(!cur||matchMedia(\'(prefers-reduced-motion:reduce)\').matches){show(id);return;}\n  const rapido=cur.classList.contains(\'out\');\n  cur.classList.add(\'out\');                          // se desvanece suave\n  setTimeout(()=>{\n    if(my!==run)return;\n    cur.classList.remove(\'out\');\n    show(target);                                    // y entra la nueva sección\n  },rapido?0:160);\n}\n\ndocument.addEventListener(\'click\',e=>{\n  const b=e.target.closest(\'[data-go]\');\n  if(b)go(b.dataset.go);\n});\n\n// Opciones en 3D: se inclinan hacia donde está el mouse\ndocument.querySelectorAll(\'nav button\').forEach(b=>{\n  b.addEventListener(\'pointermove\',e=>{\n    if(e.pointerType!==\'mouse\'||matchMedia(\'(prefers-reduced-motion:reduce)\').matches)return;\n    const x=e.offsetX/b.offsetWidth,y=e.offsetY/b.offsetHeight;\n    b.style.setProperty(\'--ry\',((x-.5)*24).toFixed(1)+\'deg\');\n    b.style.setProperty(\'--rx\',((.5-y)*18).toFixed(1)+\'deg\');\n    b.style.setProperty(\'--gx\',Math.round(x*100)+\'%\');\n    b.style.setProperty(\'--gy\',Math.round(y*100)+\'%\');\n  });\n  b.addEventListener(\'pointerleave\',()=>{b.style.removeProperty(\'--rx\');b.style.removeProperty(\'--ry\');});\n});\n\n// Fondo: el color cambia por donde pasa el mouse\nconst glow=document.querySelector(\'.glow\');\nlet tx=0,ty=0,cx=0,cy=0,raf=0,hue=null;\nfunction pintar(){\n  const k=matchMedia(\'(prefers-reduced-motion:reduce)\').matches?1:.14;\n  cx+=(tx-cx)*k;cy+=(ty-cy)*k;\n  glow.style.transform=\'translate3d(\'+cx+\'px,\'+cy+\'px,0)\';\n  const h=Math.round(-14+cx/innerWidth*28+cy/innerHeight*8);\n  if(h!==hue){hue=h;glow.style.filter=\'hue-rotate(\'+h+\'deg)\';}\n  raf=Math.abs(tx-cx)+Math.abs(ty-cy)>.5?requestAnimationFrame(pintar):0;\n}\nfunction mover(e){\n  tx=e.clientX;ty=e.clientY;\n  if(!glow.classList.contains(\'on\')){cx=tx;cy=ty;glow.classList.add(\'on\');}\n  if(!raf)raf=requestAnimationFrame(pintar);\n}\naddEventListener(\'pointermove\',mover,{passive:true});\naddEventListener(\'pointerdown\',mover,{passive:true});\n\n// Esqueleto mientras carga (sobre todo si no hay internet)\nconst skel=document.getElementById(\'skel\');\nfunction quitarEsqueleto(){\n  document.documentElement.classList.remove(\'cargando\');\n  skel.classList.add(\'fuera\');\n  setTimeout(()=>skel.remove(),450);\n}\nPromise.race([\n  gfDone.then(()=>Promise.all([document.fonts.load(\'700 1em Sora\'),document.fonts.load(\'400 1em Montserrat\')])),\n  new Promise(r=>setTimeout(r,4000))\n]).catch(()=>{}).then(()=>{\n  const sinRed=gfFail||!navigator.onLine;\n  setTimeout(quitarEsqueleto,sinRed?Math.max(0,700-performance.now()):0);\n});\n\n// Carrusel antes / después (cambia estos datos por tus resultados reales)\nconst casos=[\n  {pl:\'TikTok\',t:\'Receta en 30 s\',g:["tiktokgif1.gif","tiktokgif2.gif"],a:[100,56,34,23,17,13],d:[100,90,82,76,71,67],m:[[\'Retención a 3 s\',\'41%\',\'78%\'],[\'Vista promedio\',\'4 s\',\'11 s\']]},\n  {pl:\'Reels\',t:\'Antes de tu viaje\',g:["gifcolors1.gif","gifcolors2.gif"],a:[100,60,38,27,20,15],d:[100,93,85,79,74,70],m:[[\'Retención a 3 s\',\'45%\',\'81%\'],[\'Vista promedio\',\'5 s\',\'12 s\']]},\n  {pl:\'Shorts\',t:\'Tu producto en 15 s\',g:["Shortsgif1.gif","Shortsgif2.gif"],a:[100,52,31,20,14,10],d:[100,88,80,73,68,64],m:[[\'Retención a 3 s\',\'38%\',\'75%\'],[\'Vista promedio\',\'3 s\',\'9 s\']]}\n];\nconst pts=v=>v.map((y,i)=>(i?\'L\':\'M\')+i*48+\',\'+(110-y)).join(\'\');\nconst track=document.getElementById(\'baTrack\'),view=document.getElementById(\'baView\'),dots=document.getElementById(\'baDots\');\ntrack.innerHTML=casos.map(c=>`\n<article class="ba-slide">\n  <div class="ph"><div class="ph-a">${c.g?`<img data-g="${c.g[0]}" alt="Antes" draggable="false" decoding="async" onerror="this.hidden=true">`:`<small>${c.t.toLowerCase()}</small>`}</div><div class="ph-d"><div class="ph-i">${c.g?`<img data-g="${c.g[1]}" alt="Después" draggable="false" decoding="async" onerror="this.hidden=true">`:c.t}</div></div><span class="tg l">Antes</span><span class="tg r">Después</span></div>\n  <div class="ba-r">\n    <h3>${c.pl}: ${c.t}</h3>\n    <svg class="ch" viewBox="0 0 240 120" role="img" aria-label="Curva de retención antes y después">\n      <path d="M0 10H240M0 60H240M0 110H240" fill="none" stroke="currentColor" stroke-opacity=".14"/>\n      <path class="ln a" pathLength="1" d="${pts(c.a)}"/>\n      <path class="ln d" pathLength="1" d="${pts(c.d)}"/>\n    </svg>\n    <p class="lg"><span><i></i>Antes</span><span><i class="d"></i>Después</span></p>\n    <div class="mets">${c.m.map(([n,a,d])=>`<div><small>${n}</small><b><i>${a}</i> → <em>${d}</em></b></div>`).join(\'\')}</div>\n  </div>\n</article>`).join(\'\');\ndots.innerHTML=casos.map((c,i)=>`<button type="button" aria-label="Ver ${c.pl}" data-bi="${i}"></button>`).join(\'\');\nconst slides=[...track.children];\nlet bi=0,pausa=false,visible=false;\n// GIFs: solo corre el de la diapositiva visible, y el "antes" y el "después" arrancan en el mismo instante\nconst gifBlobs={};\nfunction gifMs(buf){\n  const d=new Uint8Array(buf);let p=13,ms=0;\n  if(d[10]&128)p+=3<<((d[10]&7)+1);\n  while(p<d.length){\n    const t=d[p++];\n    if(t===0x3B)break;\n    if(t===0x21){\n      if(d[p++]===0xF9){const c=d[p+2]|(d[p+3]<<8);ms+=(c<2?10:c)*10;}\n      while(p<d.length&&d[p])p+=d[p]+1;\n      p++;\n    }else if(t===0x2C){\n      const f=d[p+8];p+=9;\n      if(f&128)p+=3<<((f&7)+1);\n      p++;\n      while(p<d.length&&d[p])p+=d[p]+1;\n      p++;\n    }else break;\n  }\n  return ms;\n}\nfunction gifBlob(u){\n  return gifBlobs[u]||(gifBlobs[u]=fetch(u).then(r=>r.ok?r.arrayBuffer():Promise.reject())\n    .then(buf=>({b:new Blob([buf],{type:\'image/gif\'}),ms:gifMs(buf)}))\n    .catch(e=>{delete gifBlobs[u];throw e;}));\n}\nfunction gifSoltar(i){const o=i.getAttribute(\'src\');if(o&&o.startsWith(\'blob:\'))URL.revokeObjectURL(o);}\nfunction gifLanzar(im,d){\n  im.forEach(gifSoltar);\n  im.forEach((i,k)=>{i.hidden=false;i.src=URL.createObjectURL(d[k].b);});\n}\nfunction gifsArrancar(s){\n  const im=[...s.querySelectorAll(\'img[data-g]\')];\n  if(!im.length)return;\n  s._on=true;const tok=s._k=(s._k||0)+1;\n  Promise.all(im.map(i=>gifBlob(i.dataset.g))).then(d=>{\n    if(!s._on||s._k!==tok)return;\n    gifLanzar(im,d);\n    const T=Math.max(...d.map(x=>x.ms));\n    if(T&&d.some(x=>Math.abs(x.ms-T)>30))s._rs=setInterval(()=>{if(s._on&&s._k===tok)gifLanzar(im,d);},T);\n  }).catch(()=>{if(s._on&&s._k===tok)im.forEach(i=>{i.src=i.dataset.g;});});\n}\nfunction gifsParar(s){\n  s._on=false;s._k=(s._k||0)+1;clearInterval(s._rs);\n  s.querySelectorAll(\'img[data-g]\').forEach(i=>{gifSoltar(i);i.removeAttribute(\'src\');});\n}\nfunction gifs(){\n  slides.forEach((s,k)=>{\n    clearTimeout(s._t);\n    if(k===bi&&visible&&!document.hidden){if(!s._on)gifsArrancar(s);}\n    else if(s._on)s._t=setTimeout(()=>gifsParar(s),550);\n  });\n  if(visible)slides[(bi+1)%slides.length].querySelectorAll(\'img[data-g]\').forEach(i=>gifBlob(i.dataset.g).catch(()=>{}));\n}\nfunction irA(i){\n  bi=(i+slides.length)%slides.length;\n  track.style.transform=\'translateX(\'+(-bi*100)+\'%)\';\n  slides.forEach((s,k)=>s.classList.toggle(\'on\',k===bi));\n  [...dots.children].forEach((d,k)=>d.setAttribute(\'aria-current\',k===bi));\n  gifs();\n}\nirA(0);\nif(\'IntersectionObserver\' in window)new IntersectionObserver(e=>{visible=e[e.length-1].isIntersecting;gifs();}).observe(view);else{visible=true;gifs();}\ndocument.addEventListener(\'visibilitychange\',gifs);\nif(!matchMedia(\'(prefers-reduced-motion:reduce)\').matches){\n  setInterval(()=>{if(!pausa&&!document.hidden&&view.offsetParent)irA(bi+1);},5200);\n}\nview.addEventListener(\'pointerenter\',()=>pausa=true);\nview.addEventListener(\'pointerleave\',()=>pausa=false);\ndocument.addEventListener(\'click\',e=>{\n  const n=e.target.closest(\'[data-ba]\'),d=e.target.closest(\'[data-bi]\');\n  if(n)irA(bi+Number(n.dataset.ba));\n  if(d)irA(Number(d.dataset.bi));\n});\nlet sx=null;\nview.addEventListener(\'pointerdown\',e=>{\n  const ph=e.target.closest(\'.ph\');\n  if(!ph){sx=e.clientX;return;}\n  sx=null;\n  const arrastrar=ev=>{\n    const r=ph.getBoundingClientRect();\n    ph.classList.add(\'man\');\n    ph.style.setProperty(\'--p\',Math.max(4,Math.min(96,(ev.clientX-r.left)/r.width*100))+\'%\');\n  };\n  const fin=()=>{\n    removeEventListener(\'pointermove\',arrastrar);removeEventListener(\'pointerup\',fin);\n    setTimeout(()=>{ph.classList.remove(\'man\');ph.style.removeProperty(\'--p\');},2500);\n  };\n  arrastrar(e);\n  addEventListener(\'pointermove\',arrastrar);addEventListener(\'pointerup\',fin);\n});\nview.addEventListener(\'pointerup\',e=>{\n  if(sx===null)return;\n  const dx=e.clientX-sx;sx=null;\n  if(Math.abs(dx)>50)irA(bi+(dx<0?1:-1));\n});\n\n// Modo claro / oscuro: sigue la configuración del sistema\nconst raiz=document.documentElement,mqClaro=matchMedia(\'(prefers-color-scheme:light)\');\nmqClaro.addEventListener(\'change\',()=>{raiz.dataset.theme=mqClaro.matches?\'light\':\'dark\';});\n</script>\n</body>\n</html>\n'


def _id_tiktok(url):
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else ""


def _alt(url):
    # Respaldo: si el servidor no logra la miniatura, la página intenta esta dirección directamente
    ident = _id_tiktok(url)
    if "tiktok.com" in url and ident:
        return f"https://www.tiktok.com/api/img/?itemId={ident}&location=0&aid=1988"
    return ""


# Los trabajos viajan a la página como datos
HTML = HTML.replace(
    "__TRABAJOS__",
    json.dumps([dict(t, alt=_alt(t["url"])) for t in TRABAJOS], ensure_ascii=False).replace("</", "<\\/"),
)

CARPETA = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(CARPETA, "miniaturas")
UA_NAVEGADOR = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
UA_FACEBOOK = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
TIPOS_IMG = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
EXT_IMG = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/avif": ".avif", "image/gif": ".gif"}

_cache = {}
_locks = [threading.Lock() for _ in TRABAJOS]


def _descargar(url, ua=UA_NAVEGADOR, referer=None, limite=8_000_000):
    cab = {"User-Agent": ua, "Accept-Language": "es,en;q=0.8", "Accept": "*/*"}
    if referer:
        cab["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=12) as r:
        return r.read(limite), r.headers.get("Content-Type", "")


def _tipo_img(b):
    """Reconoce la imagen por sus primeros bytes (no confía en lo que diga el servidor)."""
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if b[4:8] == b"ftyp" and b[8:12] in (b"avif", b"avis"):
        return "image/avif"
    return ""


def _meta(pagina, nombre):
    for m in re.finditer(r"<meta\s[^>]*>", pagina, re.I):
        tag = m.group(0)
        if re.search(r"""(?:property|name)\s*=\s*["']%s["']""" % re.escape(nombre), tag, re.I):
            c = re.search(r"""content\s*=\s*(?:"([^"]*)"|'([^']*)')""", tag, re.I)
            if c:
                return unescape(c.group(1) or c.group(2) or "")
    return ""


def _limpiar(texto):
    texto = re.sub(r"#\S+", "", texto or "")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto if len(texto) <= 70 else texto[:69].rstrip() + "\u2026"


def _pagina(url, ua):
    p = _descargar(url, ua=ua)[0].decode("utf-8", "ignore")
    return _limpiar(_meta(p, "og:title")), _meta(p, "og:image") or _meta(p, "twitter:image")


def _tiktok_oembed(url):
    j = json.loads(_descargar("https://www.tiktok.com/oembed?url=" + urllib.parse.quote(url, safe=""))[0])
    return _limpiar(j.get("title")) or j.get("author_name", ""), j.get("thumbnail_url", "")


def _tiktok_datos(url):
    p = _descargar(url)[0].decode("utf-8", "ignore")
    m = re.search(r'"(?:originCover|cover|dynamicCover)"\s*:\s*"(https:[^"]+)"', p)
    return "", (json.loads('"' + m.group(1) + '"') if m else "")


def _yt_dlp(url):
    import yt_dlp  # opcional: pip install yt-dlp

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, "socket_timeout": 15}) as y:
        info = y.extract_info(url, download=False)
    todas = info.get("thumbnails") or []
    return _limpiar(info.get("title")), info.get("thumbnail") or (todas[-1].get("url", "") if todas else "")


def _estrategias(url):
    """Formas de averiguar (titulo, direccion_de_miniatura), de la más a la menos fiable."""
    if "tiktok.com" in url:
        yield "oEmbed de TikTok", lambda: _tiktok_oembed(url)
        yield "vista previa de la página", lambda: _pagina(url, UA_FACEBOOK)
        yield "datos de la página", lambda: _tiktok_datos(url)
        if _alt(url):
            yield "api/img de TikTok", lambda: ("", _alt(url))
    else:
        yield "vista previa de la página", lambda: _pagina(url, UA_FACEBOOK)
        yield "página como navegador", lambda: _pagina(url, UA_NAVEGADOR)
    yield "yt-dlp", lambda: _yt_dlp(url)


def _clave(i):
    return hashlib.md5(TRABAJOS[i]["url"].encode("utf-8")).hexdigest()[:10]


def _de_disco(i):
    for tipo, ext in EXT_IMG.items():
        ruta = os.path.join(CACHE, _clave(i) + ext)
        if os.path.isfile(ruta):
            with open(ruta, "rb") as f:
                return f.read(), tipo
    return None


def _a_disco(i, img, tipo):
    try:
        os.makedirs(CACHE, exist_ok=True)
        with open(os.path.join(CACHE, _clave(i) + EXT_IMG[tipo]), "wb") as f:
            f.write(img)
    except OSError:
        pass


def _datos(i):
    """(titulo, imagen, tipo) del trabajo i. La miniatura queda guardada en miniaturas/ para no bajarla de nuevo."""
    with _locks[i]:
        previo = _cache.get(i)
        if previo and (previo[0] or previo[1] or time.time() - previo[3] < 60):
            return previo[:3]
        titulo, img, tipo = "", None, ""
        guardada = _de_disco(i)
        if guardada:
            img, tipo = guardada
        else:
            url = TRABAJOS[i]["url"]
            origen = urllib.parse.urlsplit(url)
            ref = f"{origen.scheme}://{origen.netloc}/"
            errores = []
            for nombre, buscar in _estrategias(url):
                try:
                    t, miniatura = buscar()
                    titulo = titulo or t
                    if not miniatura:
                        raise ValueError("no trajo miniatura")
                    datos = _descargar(miniatura, referer=ref)[0]
                    tipo = _tipo_img(datos)
                    if not tipo:
                        raise ValueError("lo descargado no es una imagen válida")
                    img = datos
                    _a_disco(i, img, tipo)
                    print(f"[Trabajo {i + 1}] miniatura lista ({nombre})")
                    break
                except Exception as e:
                    tipo = ""
                    errores.append(f"{nombre}: {e}")
            if img is None:
                print(f"[Trabajo {i + 1}] no se pudo traer la miniatura. Intentos -> " + " | ".join(errores))
                print(f"   Solución segura: guarda una captura del video como trabajo{i + 1}.jpg junto a este archivo.")
        _cache[i] = (titulo, img, tipo, time.time())
        return titulo, img, tipo


def _precargar(i):
    try:
        if _imagen_propia(i) and TRABAJOS[i]["titulo"]:
            return
        _datos(i)
    except Exception as e:
        print(f"[Trabajo {i + 1}] error inesperado: {e}")


def _imagen_propia(i):
    for ext, tipo in TIPOS_IMG.items():
        ruta = os.path.join(CARPETA, f"trabajo{i + 1}{ext}")
        if os.path.isfile(ruta):
            with open(ruta, "rb") as f:
                return f.read(), tipo
    return None


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # mantiene la conexión abierta: menos espera al pedir varios archivos

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # el navegador cerró la conexión a mitad de una descarga; no pasa nada

    def _no_modificado(self, etag):
        if etag and self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True
        return False

    def _responder(self, body, tipo, etag=None):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(body)))
        if etag:
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")  # el navegador pregunta, y si no cambió usa su copia
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        ruta_url = self.path.split("?")[0]

        # Miniatura y título de cada trabajo reciente
        m = re.fullmatch(r"/(miniatura|titulo)/(\d+)", ruta_url)
        if m:
            i = int(m.group(2))
            if i >= len(TRABAJOS):
                self.send_error(404)
                return
            if m.group(1) == "titulo":
                titulo = _datos(i)[0]
                if not titulo:
                    self.send_error(404)
                    return
                self._responder(titulo.encode("utf-8"), "text/plain; charset=utf-8")
                return
            propia = _imagen_propia(i)
            if propia:
                img, tipo = propia
            else:
                _, img, tipo = _datos(i)
            if not img:
                self.send_error(404)
                return
            etag = '"' + hashlib.md5(img).hexdigest()[:16] + '"'
            if not self._no_modificado(etag):
                self._responder(img, tipo, etag)
            return

        # GIFs del carrusel
        nombre = os.path.basename(ruta_url)
        if nombre.lower().endswith(".gif"):
            ruta = os.path.join(CARPETA, nombre)
            if not os.path.isfile(ruta):
                self.send_error(404)
                return
            st = os.stat(ruta)
            etag = '"%x-%x"' % (st.st_mtime_ns, st.st_size)
            if self._no_modificado(etag):
                return
            with open(ruta, "rb") as f:
                self._responder(f.read(), "image/gif", etag)
            return

        self._responder(HTML.encode("utf-8"), "text/html; charset=utf-8")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    for n in range(len(TRABAJOS)):  # trae las miniaturas mientras se abre la página
        threading.Thread(target=_precargar, args=(n,), daemon=True).start()
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as server:
        url = f"http://127.0.0.1:{PORT}"
        print(f"Sitio en {url}  (Ctrl+C para cerrar)")
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass