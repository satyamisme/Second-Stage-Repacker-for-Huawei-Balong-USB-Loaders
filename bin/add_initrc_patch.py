# add_initrc_patch.py
import sys, os

INITRC = None
args = sys.argv[1:]
for i, a in enumerate(args):
    if a == "--initrc" and i+1 < len(args):
        INITRC = args[i+1]

if not INITRC:
    print("Usage: python add_initrc_patch.py --initrc path\\init.rc")
    sys.exit(1)

if not os.path.exists(INITRC):
    print(f"ERROR: File not found: {INITRC}")
    sys.exit(1)

# FIXED: Use /bin/busybox instead of /system/bin/busybox
svc = "\nservice patchblocked /bin/busybox sh /etc/patchblocked.sh boot\n    class main\n    oneshot\n    user root\n"

with open(INITRC,"r") as f:
    content = f.read()

if "patchblocked" in content:
    print("init.rc already patched - skipping")
else:
    idx = content.find("\nservice ")
    if idx != -1:
        content = content[:idx] + svc + content[idx:]
    else:
        content = content + svc
    with open(INITRC,"w") as f:
        f.write(content)
    print(f"init.rc patched: {INITRC}")