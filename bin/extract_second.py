#!/usr/bin/env python3
# extract_second.py v2.0
import os, sys, struct, zlib

def pages(sz,pg): return (sz+pg-1)//pg
def find_android(data):
    off=data.rfind(b"ANDROID!")
    if off==-1: raise RuntimeError("ANDROID! not found")
    return off
def parse_header(data,off):
    pg=struct.unpack_from("<I",data,off+0x24)[0]
    if not(0<pg<=65536): pg=2048
    ks=struct.unpack_from("<I",data,off+0x08)[0]
    rs=struct.unpack_from("<I",data,off+0x10)[0]
    ss=struct.unpack_from("<I",data,off+0x18)[0]
    ro=off+(1+pages(ks,pg))*pg
    so=off+(1+pages(ks,pg)+pages(rs,pg))*pg
    return dict(ks=ks,rs=rs,ss=ss,pg=pg,ro=ro,so=so)
def decompress_gz(data,off,size):
    raw=bytes(data[off:off+size+65536])
    idx=raw.find(b"\x1f\x8b")
    if idx==-1: raise RuntimeError("gzip not found near second_off")
    d=zlib.decompressobj(47); return d.decompress(raw[idx:],32*1024*1024)
def parse_cpio(cpio,out_dir):
    os.makedirs(out_dir,exist_ok=True)
    pos=0; count=0
    while pos<len(cpio)-110:
        if cpio[pos:pos+6] not in(b"070701",b"070702"): break
        mode    =int(cpio[pos+14:pos+22],16)
        mtime   =int(cpio[pos+46:pos+54],16)
        filesize=int(cpio[pos+54:pos+62],16)
        namesize=int(cpio[pos+94:pos+102],16)
        ns=pos+110
        name=cpio[ns:ns+namesize-1].decode("latin1",errors="replace")
        he=(ns+namesize+3)&~3; ds=he; de=ds+filesize; dea=(de+3)&~3
        if name=="TRAILER!!!": break
        ftype=mode&0o170000
        full=os.path.join(out_dir,name.replace("/",os.sep))
        par=os.path.dirname(full)
        if par: os.makedirs(par,exist_ok=True)
        if ftype==0o040000:
            os.makedirs(full,exist_ok=True)
            if mtime: os.utime(full,(mtime,mtime))
            print(f"  {name}")
        elif ftype==0o120000:
            target=cpio[ds:de].decode("latin1",errors="replace")
            stub=full+".symlink"
            open(stub,"w",newline="\n").write(target)
            if mtime: os.utime(stub,(mtime,mtime))
            print(f"  {name}")
        elif ftype==0o100000:
            open(full,"wb").write(bytes(cpio[ds:de]))
            if mtime: os.utime(full,(mtime,mtime))
            print(f"  {name}")
        count+=1; pos=dea
    return count
def main():
    BIN=OUT=None; args=sys.argv[1:]; i=0
    while i<len(args):
        if args[i]=="--bin" and i+1<len(args): BIN=args[i+1];i+=2
        elif args[i]=="--out" and i+1<len(args): OUT=args[i+1];i+=2
        else: i+=1
    if not BIN or not OUT: print("Usage: extract_second.py --bin FILE --out DIR"); sys.exit(1)
    if not os.path.exists(BIN): print(f"ERROR: {BIN}"); sys.exit(1)
    print(f"Input : {BIN}"); print(f"Output: {OUT}")
    data=bytearray(open(BIN,"rb").read())
    print(f"Loaded: {len(data)} bytes")
    aoff=find_android(data); h=parse_header(data,aoff)
    print(f"ANDROID! at: 0x{aoff:X}")
    print(f"  kernel_size  : 0x{h['ks']:X}")
    print(f"  ramdisk_size : 0x{h['rs']:X}")
    print(f"  second_size  : 0x{h['ss']:X}")
    print(f"  page_size    : 0x{h['pg']:X}")
    print(f"  second_off   : 0x{h['so']:X} (derived)")
    raw=bytes(data[h['so']:h['so']+8])
    print(f"  magic bytes  : {raw.hex()}")
    print(f"  magic ascii  : {''.join(chr(b) if 32<=b<127 else '.' for b in raw)}")
    print(f"  Format: gzip-compressed CPIO")
    cpio=decompress_gz(data,h['so'],h['ss'])
    print(f"  Decompressed: {len(cpio)} bytes")
    print("  .")
    count=parse_cpio(cpio,OUT)
    open(os.path.join(OUT,".extract_meta"),"w").write(
        f"ANDROID_OFF=0x{aoff:X}\nSECOND_OFF=0x{h['so']:X}\nSECOND_SIZE=0x{h['ss']:X}\n"
        f"RAMDISK_OFF=0x{h['ro']:X}\nRAMDISK_SIZE=0x{h['rs']:X}\nPAGE_SIZE=0x{h['pg']:X}\nKERNEL_SIZE=0x{h['ks']:X}\n")
    print(f"\nExtracted {count} entries to: {OUT}")
    print(f"SECOND_OFF=0x{h['so']:X}  SECOND_SIZE=0x{h['ss']:X}")
if __name__=="__main__": main()
