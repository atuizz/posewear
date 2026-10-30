#!/usr/bin/env python3
"""部署后向 IndexNow 提交 URL。
用法：python3 scripts/indexnow.py            # 提交与上次相比新增/变化的页面（首次为全部）
      python3 scripts/indexnow.py --all      # 提交全部
依赖 build.py 生成的 urls.txt 与 dist/，状态存在 .indexnow-state.json。"""
import json,sys,os,hashlib,urllib.request
SITE=os.environ.get('POSEWEAR_SITE','https://posewear.pages.dev').rstrip('/');HOST=SITE.split('://',1)[1]
os.chdir(os.path.dirname(os.path.abspath(__file__))+'/..')
KEY=open('indexnow.key').read().strip()
urls=[u for u in open('urls.txt').read().split() if u]
def fp(u):
  p='dist'+u[len(SITE):]+('index.html' if u.endswith('/') else '')
  return hashlib.sha1(open(p,'rb').read()).hexdigest() if os.path.exists(p) else ''
st=json.load(open('.indexnow-state.json')) if os.path.exists('.indexnow-state.json') else {}
cur={u:fp(u) for u in urls}
todo=urls if '--all' in sys.argv or not st else [u for u in urls if st.get(u)!=cur[u]]
print(len(todo),'URLs to submit')
ok=True
for i in range(0,len(todo),10000):
  body=json.dumps({'host':HOST,'key':KEY,'keyLocation':f'{SITE}/{KEY}.txt','urlList':todo[i:i+10000]}).encode()
  rq=urllib.request.Request('https://api.indexnow.org/indexnow',body,{'Content-Type':'application/json; charset=utf-8'})
  try:
    r=urllib.request.urlopen(rq,timeout=60);print('HTTP',r.status,r.read()[:200])
  except urllib.error.HTTPError as e: print('HTTP',e.code,e.read()[:300]);ok=e.code in(200,202)
if ok: json.dump(cur,open('.indexnow-state.json','w'))
