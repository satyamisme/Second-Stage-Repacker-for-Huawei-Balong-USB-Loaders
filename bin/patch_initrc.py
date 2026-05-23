#!/usr/bin/env python3
# patch_initrc.py v2.0
import os, sys, re, shutil
def patch(initrc_path):
    if not os.path.exists(initrc_path): print(f"ERROR: {initrc_path} not found"); return False
    content=open(initrc_path,"r",errors="replace").read()
    if "patchblocked" in content: print("init.rc already patched, skipping."); return True
    INJECT="\n    exec /etc/patchblocked.sh\n"
    if re.search(r'^on boot\s*$',content,re.MULTILINE):
        content=re.sub(r'(^on boot\s*$)',r'\1'+INJECT,content,count=1,flags=re.MULTILINE)
        print("  Injected after 'on boot'")
    elif re.search(r'^on init\s*$',content,re.MULTILINE):
        content=re.sub(r'(^on init\s*$)',r'\1'+INJECT,content,count=1,flags=re.MULTILINE)
        print("  Injected after 'on init'")
    else:
        content+=f"\non boot\n{INJECT}\n"; print("  Appended 'on boot' section at end")
    shutil.copy2(initrc_path,initrc_path+".orig")
    open(initrc_path,"w",newline="\n").write(content)
    print(f"init.rc patched: {initrc_path}"); print(f"Backup: {initrc_path}.orig"); return True
def main():
    initrc=None; args=sys.argv[1:]; i=0
    while i<len(args):
        if args[i]=="--initrc" and i+1<len(args): initrc=args[i+1];i+=2
        else: i+=1
    if not initrc: print("Usage: patch_initrc.py --initrc <path>"); sys.exit(1)
    sys.exit(0 if patch(initrc) else 1)
if __name__=="__main__": main()
