#!/usr/bin/env python3
# repack_inject.py v2.1 — FIXED: no second stage offset recalculation
import os, sys, gzip, struct, io

VERSION="2.1"
print(f"repack_inject.py v{VERSION}")

S_IFDIR=0o040000; S_IFREG=0o100000; S_IFLNK=0o120000; S_ISUID=0o004000

EXEC_DIRS={"bin","sbin","usr/bin","usr/sbin","usr/bin/usb","etc/init.d",
           "system/bin","system/sbin","system/xbin"}
EXEC_NAMES={"init","ueventd","healthd","adbd","sh","busybox","watchdogd","mdev",
            "oem-nck","xsleep","usb_composition","rcS","usb","target","huaweidload",
            "linuxrc","boot_hsic_composition","boot_hsusb_composition","start","stop"}
EXEC_EXTS={".sh",".rc",".py",".elf"}

def get_mode(relpath):
    rp=relpath.replace(os.sep,"/")
    parts=rp.split("/")
    base=parts[-1]
    clean=base[:-len(".symlink")] if base.endswith(".symlink") else base
    parent="/".join(parts[:-1])
    if clean=="init" and len(parts)==1:
        return S_IFREG|S_ISUID|0o755
    if parent in EXEC_DIRS:
        return S_IFREG|0o755
    if clean in EXEC_NAMES:
        return S_IFREG|0o755
    if os.path.splitext(clean)[1].lower() in EXEC_EXTS:
        return S_IFREG|0o755
    return S_IFREG|0o644

def get_mtime(p):
    try:
        return int(os.stat(p).st_mtime)
    except:
        return 0

_ino=[1]
def next_ino():
    v=_ino[0]
    _ino[0]+=1
    return v

def cpio_entry(name,data,mode,mtime=0):
    ino=next_ino()
    nb=name.encode("latin1")+b"\x00"
    ns=len(nb)
    fs=len(data)
    hdr=(b"070701"+f"{ino:08X}".encode()+f"{mode:08X}".encode()
        +b"00000000"+b"00000000"+b"00000001"+f"{mtime:08X}".encode()
        +f"{fs:08X}".encode()+b"00000003"+b"00000001"
        +b"00000000"+b"00000000"+f"{ns:08X}".encode()+b"00000000")
    raw=hdr+nb
    raw+=b"\x00"*(-(110+ns)%4)
    raw+=data
    raw+=b"\x00"*(-fs%4)
    return raw

def build_gz(src_dir):
    _ino[0]=1
    cpio=b""
    entries=[]
    for root,dirs,files in os.walk(src_dir,followlinks=False):
        dirs.sort()
        rd=os.path.relpath(root,src_dir)
        if rd!=".":
            entries.append(("dir",rd,root))
        for f in sorted(files):
            fp=os.path.join(root,f)
            rp=os.path.relpath(fp,src_dir)
            entries.append(("file",rp,fp))
    for kind,relpath,fullpath in entries:
        cn=relpath.replace(os.sep,"/")
        mt=get_mtime(fullpath)
        try:
            if kind=="dir":
                cpio+=cpio_entry(cn,b"",S_IFDIR|0o755,mt)
                print(f"  dir  {cn}")
            elif os.path.basename(fullpath).endswith(".symlink"):
                target=open(fullpath,"r",errors="replace").read().strip()
                entry=cn[:-len(".symlink")]
                cpio+=cpio_entry(entry,target.encode("latin1"),S_IFLNK|0o777,mt)
                print(f"  lnk  {entry} -> {target}")
            elif os.path.islink(fullpath):
                target=os.readlink(fullpath)
                cpio+=cpio_entry(cn,target.encode("latin1"),S_IFLNK|0o777,mt)
                print(f"  lnk  {cn} -> {target}")
            else:
                data=open(fullpath,"rb").read()
                mode=get_mode(relpath)
                cpio+=cpio_entry(cn,data,mode,mt)
                mstr="4755" if(mode&S_ISUID) else oct(mode&0o7777)[-4:]
                print(f"  {mstr} {cn}")
        except Exception as e:
            print(f"  WARN {cn}: {e}")
    cpio+=cpio_entry("TRAILER!!!",b"",0,0)
    buf=io.BytesIO()
    with gzip.GzipFile(fileobj=buf,mode="wb",compresslevel=9,mtime=0) as gz:
        gz.write(cpio)
    return buf.getvalue()

def pages(sz,pg):
    return (sz+pg-1)//pg

def read_hdr(data,aoff):
    pg=struct.unpack_from("<I",data,aoff+0x24)[0]
    if not(0<pg<=65536):
        pg=2048
    ks=struct.unpack_from("<I",data,aoff+0x08)[0]
    rs=struct.unpack_from("<I",data,aoff+0x10)[0]
    ss=struct.unpack_from("<I",data,aoff+0x18)[0]
    ro=aoff+(1+pages(ks,pg))*pg
    so=aoff+(1+pages(ks,pg)+pages(rs,pg))*pg
    return dict(ks=ks,rs=rs,ss=ss,pg=pg,ro=ro,so=so)

def find_gz(data,expected):
    lo=max(0,expected-4096)
    hi=min(len(data),expected+16384)
    idx=bytes(data[lo:hi]).find(b"\x1f\x8b")
    if idx!=-1:
        f=lo+idx
        if f!=expected:
            print(f"    gzip at 0x{f:X} (expected 0x{expected:X})")
        return f
    for mg in(b"070701",b"070702"):
        idx=bytes(data[lo:hi]).find(mg)
        if idx!=-1:
            print(f"    raw CPIO at 0x{lo+idx:X}")
            return lo+idx
    return expected

def inject(data,aoff,off,gz,hdr_field,orig_sz,label):
    actual=find_gz(data,off)
    new_sz=len(gz)
    print(f"  {label}: {orig_sz:#x} ({orig_sz:,}B)  new={new_sz:#x} ({new_sz:,}B)",end="")
    end=actual+new_sz
    if end>len(data):
        ext=end-len(data)
        data+=bytearray(ext)
        print(f"  [binary extended +{ext:,}B]",end="")
    elif new_sz<orig_sz:
        data[actual+new_sz:actual+orig_sz]=b"\x00"*(orig_sz-new_sz)
    print()
    data[actual:actual+new_sz]=gz
    struct.pack_into("<I",data,aoff+hdr_field,new_sz)
    print(f"  {label}: injected at 0x{actual:X}  header[{hdr_field:#x}]={new_sz:#x}")
    return data

def main():
    RD=SD=BIN=OUT=None
    i=0
    args=sys.argv[1:]
    while i<len(args):
        a=args[i]
        if a=="--ramdisk" and i+1<len(args):
            RD=args[i+1]
            i+=2
        elif a=="--second" and i+1<len(args):
            SD=args[i+1]
            i+=2
        elif a=="--bin" and i+1<len(args):
            BIN=args[i+1]
            i+=2
        elif a=="--out" and i+1<len(args):
            OUT=args[i+1]
            i+=2
        else:
            i+=1
    if not BIN or not OUT:
        print("Usage: repack_inject.py --bin FILE --out FILE [--ramdisk DIR] [--second DIR]")
        sys.exit(1)
    if not RD and not SD:
        print("ERROR: need --ramdisk and/or --second")
        sys.exit(1)
    if not os.path.exists(BIN):
        print(f"ERROR: {BIN}")
        sys.exit(1)
    print(f"Binary : {BIN}")
    print(f"Output : {OUT}")
    if RD:
        print(f"Ramdisk: {RD}")
    if SD:
        print(f"Second : {SD}")
    data=bytearray(open(BIN,"rb").read())
    aoff=bytes(data).rfind(b"ANDROID!")
    if aoff==-1:
        print("ERROR: ANDROID! not found")
        sys.exit(1)
    h=read_hdr(data,aoff)
    print(f"\nANDROID! at: 0x{aoff:X}")
    print(f"  kernel={h['ks']:#x}  ramdisk={h['rs']:#x}  second={h['ss']:#x}  page={h['pg']:#x}")
    print(f"  ramdisk_off=0x{h['ro']:X}  second_off=0x{h['so']:X}")
    if RD:
        print("\n=== RAMDISK ===")
        gz=build_gz(RD)
        print(f"  Compressed: {len(gz):,} bytes")
        data=inject(data,aoff,h['ro'],gz,0x10,h['rs'],"ramdisk")
    if SD:
        print("\n=== SECOND STAGE ===")
        # CRITICAL FIX: Use original second stage offset, do NOT recalculate
        new_so = h['so']
        print(f"  using original second_off: 0x{new_so:X}")
        gz=build_gz(SD)
        print(f"  Compressed: {len(gz):,} bytes")
        data=inject(data,aoff,new_so,gz,0x18,h['ss'],"second")
    os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".",exist_ok=True)
    open(OUT,"wb").write(data)
    print(f"\nSaved: {OUT}  ({len(data):,} bytes)")
    print("Done.")

if __name__=="__main__":
    main()