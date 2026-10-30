COL={'beige':'米色','black':'黑色','blue':'蓝色','brown':'棕色','burgundy':'酒红色','cream':'奶油色','gold':'金色','green':'绿色','grey':'灰色','ivory':'象牙白','khaki':'卡其色','lavender':'薰衣草紫','mint':'薄荷绿','navy':'藏青色','olive':'橄榄绿','orange':'橙色','pink':'粉色','purple':'紫色','red':'红色','silver':'银色','white':'白色','yellow':'黄色'}
MOD={'chiffon':'雪纺','corduroy':'灯芯绒','denim':'牛仔','floral':'碎花','frill':'荷叶边','fur':'毛绒','knit':'针织','lace':'蕾丝','leather':'皮质','mesh':'网纱','pleated':'百褶','polka-dot':'波点','satin':'缎面','suede':'麂皮','tulle':'薄纱','velvet':'丝绒','wool':'羊毛','ribbon':'蝴蝶结','maxi':'长款','midi':'中长','mini':'迷你'}
# noun: (zh, slot)  slots: top outer bottom one legs shoes acc
N={'blouse':('衬衫','top'),'camisole':('吊带','top'),'shirt':('衬衣','top'),'sweater':('毛衣','top'),'turtleneck':('高领毛衣','top'),'hoodie':('连帽卫衣','top'),'vest':('马甲','top'),'bra':('文胸','top'),'corset':('束腰','top'),
'cardigan':('开衫','outer'),'coat':('大衣','outer'),'jacket':('夹克','outer'),'robe':('睡袍','outer'),
'skirt':('半身裙','bottom'),'shorts':('短裤','bottom'),'pants':('长裤','bottom'),'jeans':('牛仔裤','bottom'),'briefs':('内裤','bottom'),
'dress':('连衣裙','one'),'swimsuit':('泳衣','one'),'apron':('围裙','acc'),
'socks':('袜子','legs'),'tights':('连裤袜','legs'),'stockings':('长筒袜','legs'),
'sneakers':('运动鞋','shoes'),'boots':('靴子','shoes'),'heels':('高跟鞋','shoes'),'loafers':('乐福鞋','shoes'),'pumps':('浅口鞋','shoes'),'sandals':('凉鞋','shoes'),
'bag':('手提包','acc'),'tote':('托特包','acc'),'beanie':('毛线帽','acc'),'beret':('贝雷帽','acc'),'hat':('帽子','acc'),'headband':('发箍','acc'),'belt':('腰带','acc'),'choker':('颈链','acc'),'gloves':('手套','acc'),'muffler':('围巾','acc'),'scarf':('丝巾','acc'),'necklace':('项链','acc'),'sunglasses':('墨镜','acc')}
SOLO={'knit':('针织衫','top'),'denim':('牛仔外套','outer'),'lace':('蕾丝','acc'),'fur':('毛绒披肩','outer'),'ribbon':('蝴蝶结','acc'),'leather':('皮夹克','outer'),'frill':('荷叶边','acc'),'mini':('迷你裙','bottom')}
EN_SOLO={'knit':'knit top','denim':'denim jacket','fur':'fur stole','leather':'leather jacket','mini':'miniskirt','lace':'lace trim','frill':'frills','ribbon':'ribbon'}
SKIRT_LEN={'mini':'短裙','midi':'中长裙','maxi':'长裙'}
def parse(kw):
  t=kw.split();out=[];mods=[];i=0
  for j,w in enumerate(t):
    nx=t[j+1] if j+1<len(t) else ''
    if w in SOLO and w not in N and (nx in COL) and not (w in SKIRT_LEN):
      zh,slot=SOLO[w];out.append((mods,w,zh,slot));mods=[];continue
    if w in N or (w not in COL and w not in MOD):
      zh,slot=N.get(w,(w,'acc'));out.append((mods,w,zh,slot));mods=[]
    else: mods.append(w)
  # trailing modifiers: colors apply to previous item or solo nouns
  for m in mods:
    if m in SOLO and SOLO[m][1]=='outer' and any(o[3]=='outer' for o in out): continue
    if m in SOLO: out.append(([],m,)+SOLO[m])
    elif out and m in COL: out[-1][0].append(m)
  # fix: modifier that is a SOLO noun followed by a non-related garment? keep simple
  return out
def zhp(mods,w,zh):
  if w in SOLO and w not in N: mods=[m for m in mods if m in COL]
  cs=[m for m in mods if m in COL]
  if len(cs)>1 and cs[0] in('mint','olive') and cs[1]=='green': cs=cs[:1]+cs[2:]
  if cs[:2]==['silver','grey']: cs=['SG']+cs[2:]
  c='拼'.join({'SG':'银灰色'}.get(m) or COL[m] for m in cs)
  ms=[m for m in mods if m in MOD and (w in('skirt','dress') or m not in SKIRT_LEN)]
  if w=='skirt':
    ln=[m for m in ms if m in SKIRT_LEN]; ms=[m for m in ms if m not in SKIRT_LEN]
    zh=SKIRT_LEN[ln[0]] if ln else zh
  if w=='dress':
    ln=[m for m in ms if m in SKIRT_LEN]; ms=[m for m in ms if m not in SKIRT_LEN]
    if ln: zh={'mini':'短款','midi':'中长','maxi':'长款'}[ln[0]]+zh
  m=''.join(MOD[x] for x in ms)
  return c+m+zh
def enp(mods,w):
  if w in EN_SOLO and w not in N: return ' '.join(mods+[EN_SOLO[w]])
  base={'pants':'trousers','tote':'tote bag','muffler':'muffler','heels':'high heels'}.get(w,w)
  if w=='mini' : base='miniskirt'
  mods=[m for m in mods if w in('skirt','dress') or m not in SKIRT_LEN]
  return ' '.join(mods+[base])
def gen(kw,cat):
  items=parse(kw);S={}
  for mods,w,zh,slot in items: S.setdefault(slot,[]).append(zhp(mods,w,zh))
  J=lambda k:'与'.join(S[k]) if len(S.get(k,[]))<3 else '、'.join(S[k][:-1])+'和'+S[k][-1]
  parts=[]
  if 'one' in S: parts.append('身穿'+J('one'))
  if 'top' in S: parts.append(('内搭' if 'outer' in S else '叠搭' if 'one' in S else '上身穿')+J('top'))
  if 'outer' in S: parts.append(('外披' if 'one' in S else '外搭')+J('outer'))
  if 'bottom' in S: parts.append('下身配'+J('bottom'))
  if 'legs' in S: parts.append('搭配'+J('legs'))
  if 'shoes' in S: parts.append('脚踩'+J('shoes'))
  if 'acc' in S: parts.append('再以'+J('acc')+'点缀')
  zh=('，'.join(parts) or kw)+'。'
  tags=[enp(m,w) for m,w,_,_ in items]
  en=', '.join(dict.fromkeys([cat+' outfit']+tags))
  return zh,en
if __name__=='__main__':
  import json,random
  D=json.load(open(__import__('os').environ.get('POSEWEAR_RAW','assets-raw')+'/costume/data.json'))['D'];random.seed(3)
  for d in random.sample(D,12): print(d['キーワード'],'\n  ',*gen(d['キーワード'],'x'))

# ===== v10: 去重词、变化句式、生成标题 =====
import zlib
def _clean(mods,w,zh):
  # 去掉与名词重复的修饰（denim jeans → 牛仔裤）
  mods=[m for m in mods if not (m in MOD and MOD[m] in zh)]
  return mods
def gen2(kw,cat,cid):
  items=parse(kw);S={};ORD=[]
  for mods,w,zh,slot in items:
    mods=_clean(mods,w,zh);S.setdefault(slot,[]).append(zhp(mods,w,zh))
  # 半身裙 + 短裤 同时出现 → 裙裤
  b=S.get('bottom',[])
  sk=[x for x in b if x.endswith('裙')];sh=[x for x in b if x.endswith('短裤')]
  if sk and sh and len(b)==2: S['bottom']=[sk[0][:-1]+'裙裤']
  for k in S: S[k]=list(dict.fromkeys(S[k]))
  h=zlib.crc32(cid.encode());pick=lambda opts,n:opts[(h>>n)%len(opts)]
  J=lambda k:'与'.join(S[k]) if len(S[k])<3 else '、'.join(S[k][:-1])+'和'+S[k][-1]
  P=[]
  if 'one' in S: P.append(pick(['身穿','一条','穿'],1)+J('one') if S['one'][0].endswith('裙') else '身穿'+J('one'))
  if 'top' in S: P.append(('内搭' if 'outer' in S else '叠穿' if 'one' in S else pick(['上身是','上身穿','上衣选'],3))+J('top'))
  if 'outer' in S: P.append(('外披' if 'one' in S else pick(['外搭','外面套','外穿'],5))+J('outer'))
  if 'bottom' in S: P.append(pick(['下身配','下装是','配'],7)+J('bottom'))
  if 'legs' in S: P.append(pick(['搭配','配','腿上是'],9)+J('legs'))
  if 'shoes' in S: P.append(pick(['脚踩','穿','鞋子选'],11)+J('shoes'))
  if 'acc' in S:
    a=J('acc');P.append(pick([f'再加{a}',f'配{a}',f'{a}作点缀',f'点缀{a}'],13))
  zh=('，'.join(P) or kw)+'。'
  # 标题：主件
  def short(x):return x
  if 'one' in S: main=[S['one'][0]]+(S.get('outer',[])[:1])
  else: main=(S.get('outer',[])[:1] or S.get('top',[])[:1])+S.get('bottom',[])[:1]
  if not main: main=[v[0] for v in S.values()][:2]
  t=' + '.join(main)
  if len(t)>14:
    import re
    strip=lambda x:re.sub('^('+'|'.join(sorted(set(COL.values())|{'银灰色'},key=len,reverse=True))+')+(拼('+'|'.join(COL.values())+'))*','',x) or x
    t=' + '.join(strip(x) for x in main)
  tags=[enp(m,w) for m,w,_,_ in items]
  en=', '.join(dict.fromkeys([cat+' outfit']+tags))
  return zh,en,t
