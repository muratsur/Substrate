import struct,sys,collections,re,json
b=open(sys.argv[1],'rb').read()
def fstr(o):
    l=struct.unpack_from('<i',b,o)[0]; o+=4
    if l>0: return b[o:o+l-1].decode('latin1'),o+l
    return b[o:o+(-l*2)-2].decode('utf-16le'),o+(-l*2)
NC,NO,IC,IO,EC,EO=648,728,309,28578,8015,40938
names=[];o=NO
for _ in range(NC):
    s,o=fstr(o); names.append(s); o+=4
def N(i,n=0): return names[i]+('' if n==0 else '_%d'%(n-1))
imps=[]
for i in range(IC):
    p=IO+i*40
    cp,cpn,cn,cnn,outer,on,onn,pk,pkn,opt=struct.unpack_from('<iiiiiiiiii',b,p)
    imps.append(dict(cls=N(cn,cnn),outer=outer,name=N(on,onn),pkg=N(pk,pkn)))
exps=[]
for i in range(EC):
    p=EO+i*112
    cl,sup,tmpl,outer,on,onn,flags,size,off=struct.unpack_from('<iiiiiiIqq',b,p)
    exps.append(dict(i=i+1,cls=cl,outer=outer,name=N(on,onn),size=size,off=off))
def ref(idx):
    if idx>0: return exps[idx-1]['name']
    if idx<0: return imps[-idx-1]['name']
    return None
for e in exps: e['clsname']=ref(e['cls']); e['outername']=ref(e['outer'])
json.dump(dict(imports=imps,exports=exps),open(sys.argv[2],'w'))
c=collections.Counter(e['clsname'] for e in exps)
for k,v in c.most_common(60): print(v,k)
