#!/usr/bin/env python3
# usbloader_packer.py v2.0 - with info display and safe loader creation
import os, sys, struct, configparser

HEADER_SIZE = 84
MAGIC = 0x00020000
BLOCK_DESC_OFF = 36
BLOCK_DESC_SZ = 16
MAX_BLOCKS = 10

BLOCK_NAMES = {0: "raminit", 1: "usbldr"}

# V7R22 patch signature from ulpatcher.c
V7R22_SIG = bytes([
    0x12, 0x3B, 0xA0, 0xE3, 0x4A, 0x35, 0x4A, 0xE3, 0x00, 0x20, 0xA0, 0xE3,
    0x78, 0x20, 0xC3, 0xE5, 0x79, 0x20, 0xC3, 0xE5, 0x7A, 0x20, 0xC3, 0xE5,
    0x7B, 0x20, 0xC3, 0xE5, 0x00, 0x00, 0xA0, 0xE3
])

V7R11_SIG = bytes([
    0x00, 0x00, 0x50, 0xE3, 0x70, 0x80, 0xBD, 0x08, 0x00, 0x30, 0xA0, 0xE3,
    0x4E, 0x26, 0x04, 0xE3, 0xE0, 0x3F, 0x44, 0xE3, 0x55, 0x22, 0x44, 0xE3,
    0x4C, 0x01, 0x9F, 0xE5, 0x4E, 0xC6, 0x04, 0xE3, 0x48, 0x41, 0x9F, 0xE5,
    0x02, 0x10, 0xA0, 0xE1, 0x4C, 0xC4, 0x44, 0xE3, 0x5C, 0x23, 0x83, 0xE5,
    0x00, 0x00, 0x8F, 0xE0, 0x40, 0xC3, 0x83, 0xE5
])

def show_info(loader_file):
    """Display loader structure without unpacking"""
    with open(loader_file, 'rb') as f:
        data = f.read()
    
    print(f"\n=== Loader Info: {os.path.basename(loader_file)} ===")
    print(f"File size: {len(data)} bytes")
    
    magic = struct.unpack_from("<I", data, 0)[0]
    print(f"Magic: 0x{magic:08X} ({'VALID' if magic == MAGIC else 'UNKNOWN'})")
    
    print("\nBlock descriptors:")
    for i in range(MAX_BLOCKS):
        off = BLOCK_DESC_OFF + i * BLOCK_DESC_SZ
        if off + 16 > len(data):
            break
        lmode, size, address, offset = struct.unpack_from("<IIII", data, off)
        if lmode == 0 and size == 0 and address == 0 and offset == 0:
            break
        name = BLOCK_NAMES.get(i, f"block{i}")
        print(f"  Block{i} ({name}): lmode={lmode}, size={size} bytes, "
              f"load_addr=0x{address:08X}, file_offset=0x{offset:X}")
    
    # Find ANDROID!
    aoff = data.rfind(b"ANDROID!")
    if aoff != -1:
        print(f"\nANDROID! found at: 0x{aoff:X}")
        ks = struct.unpack_from("<I", data, aoff+0x08)[0]
        rs = struct.unpack_from("<I", data, aoff+0x10)[0]
        ss = struct.unpack_from("<I", data, aoff+0x18)[0]
        pg = struct.unpack_from("<I", data, aoff+0x24)[0]
        print(f"  kernel_size: {ks} bytes")
        print(f"  ramdisk_size: {rs} bytes")
        print(f"  second_size: {ss} bytes")
        print(f"  page_size: {pg} bytes")
    else:
        print("\nANDROID! not found")
    
    return True

def make_safe_loader(input_file, output_file):
    """Apply NOP patch to disable flash erase (creates usblsafe.bin)"""
    with open(input_file, 'rb') as f:
        data = bytearray(f.read())
    
    patched = False
    
    # Try V7R22 patch
    pos = data.find(V7R22_SIG)
    if pos != -1:
        patch_pos = pos + len(V7R22_SIG) - 37
        if patch_pos + 4 <= len(data):
            data[patch_pos:patch_pos+4] = bytes([0x00, 0x00, 0xA0, 0xE1])
            print(f"Applied V7R22 patch at offset 0x{patch_pos:X}")
            patched = True
    
    # Try V7R11 patch (br-patch type 0 = NOP)
    pos = data.find(V7R11_SIG)
    if pos != -1:
        patch_pos = pos + len(V7R11_SIG) + 4
        if patch_pos + 4 <= len(data):
            data[patch_pos:patch_pos+4] = bytes([0x00, 0x00, 0xA0, 0xE1])
            print(f"Applied V7R11 patch at offset 0x{patch_pos:X}")
            patched = True
    
    if not patched:
        print("WARNING: No known patch signature found")
    
    with open(output_file, 'wb') as f:
        f.write(data)
    print(f"Safe loader saved to: {output_file}")
    return patched

def verify_repack(original_file, repacked_file):
    """Compare original and repacked loader structure"""
    with open(original_file, 'rb') as f:
        orig = f.read()
    with open(repacked_file, 'rb') as f:
        new = f.read()
    
    print(f"\n=== Verify Repack ===")
    print(f"Original: {len(orig)} bytes")
    print(f"Repacked: {len(new)} bytes")
    
    # Check magic
    orig_magic = struct.unpack_from("<I", orig, 0)[0]
    new_magic = struct.unpack_from("<I", new, 0)[0]
    print(f"Magic: 0x{orig_magic:08X} -> 0x{new_magic:08X}")
    
    # Check blocks
    all_ok = True
    for i in range(2):
        off = BLOCK_DESC_OFF + i * BLOCK_DESC_SZ
        if off + 16 > len(orig) or off + 16 > len(new):
            break
        orig_lmode, orig_size, orig_addr, orig_offset = struct.unpack_from("<IIII", orig, off)
        new_lmode, new_size, new_addr, new_offset = struct.unpack_from("<IIII", new, off)
        if orig_size == 0:
            break
        
        if orig_lmode != new_lmode:
            print(f"Block{i} lmode: {orig_lmode} -> {new_lmode} (WARNING)")
            all_ok = False
        if orig_addr != new_addr:
            print(f"Block{i} addr: 0x{orig_addr:08X} -> 0x{new_addr:08X} (WARNING)")
            all_ok = False
        print(f"Block{i} size: {orig_size} -> {new_size} bytes")
    
    # Check ANDROID!
    orig_aoff = orig.rfind(b"ANDROID!")
    new_aoff = new.rfind(b"ANDROID!")
    if orig_aoff == new_aoff:
        print(f"ANDROID! at same offset: 0x{orig_aoff:X} - OK")
    else:
        print(f"ANDROID! moved: 0x{orig_aoff:X} -> 0x{new_aoff:X} (WARNING)")
        all_ok = False
    
    if all_ok:
        print("\nVERIFICATION: PASSED - Loader structure preserved")
    else:
        print("\nVERIFICATION: WARNING - Some changes detected")
    
    return all_ok

def unpack(input_file, out_dir=None):
    if out_dir is None:
        out_dir = input_file + ".unpacked"
    os.makedirs(out_dir, exist_ok=True)

    data = open(input_file, "rb").read()
    print(f"Loaded: {input_file} ({len(data)} bytes)")

    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != MAGIC:
        print(f"WARNING: Magic mismatch! Expected 0x{MAGIC:08X}, got 0x{magic:08X}")
    else:
        print(f"Magic OK: 0x{magic:08X}")

    header = data[:HEADER_SIZE]
    open(os.path.join(out_dir, "header.bin"), "wb").write(header)
    print(f"Saved: header.bin ({len(header)} bytes)")

    blocks = []
    pos = BLOCK_DESC_OFF
    block_idx = 0
    while pos + BLOCK_DESC_SZ <= HEADER_SIZE and block_idx < MAX_BLOCKS:
        lmode, size, address, offset = struct.unpack_from("<IIII", data, pos)
        if lmode == 0 and size == 0 and address == 0 and offset == 0:
            break
        blocks.append({
            "idx": block_idx,
            "lmode": lmode,
            "size": size,
            "address": address,
            "offset": offset,
            "name": BLOCK_NAMES.get(block_idx, f"block{block_idx}"),
        })
        print(f"  Block {block_idx}: lmode={lmode} size=0x{size:X} addr=0x{address:08X} offset=0x{offset:X}")
        pos += BLOCK_DESC_SZ
        block_idx += 1

    if not blocks:
        print("ERROR: No block descriptors found!")
        return False

    cfg = configparser.ConfigParser()
    for b in blocks:
        name = b["name"]
        fname = f"block{b['idx']}_{name}.bin"
        blk_data = data[b["offset"] : b["offset"] + b["size"]]
        open(os.path.join(out_dir, fname), "wb").write(blk_data)
        print(f"Saved: {fname} ({len(blk_data)} bytes)")

        sec = f"Block{b['idx']}"
        cfg[sec] = {
            "name": name,
            "lmode": str(b["lmode"]),
            "address": f"0x{b['address']:08X}",
            "file": fname,
        }

    meta_path = os.path.join(out_dir, "metadata.txt")
    with open(meta_path, "w") as f:
        cfg.write(f)
    print(f"Saved: metadata.txt")
    print(f"\nUnpack complete -> {out_dir}/")
    return True

def pack(in_dir, output_file):
    meta_path = os.path.join(in_dir, "metadata.txt")
    header_path = os.path.join(in_dir, "header.bin")

    if not os.path.exists(meta_path):
        print(f"ERROR: metadata.txt not found in {in_dir}")
        return False

    cfg = configparser.ConfigParser()
    cfg.read(meta_path)

    if os.path.exists(header_path):
        header = bytearray(open(header_path, "rb").read())
        print(f"Using original header.bin ({len(header)} bytes)")
    else:
        header = bytearray(HEADER_SIZE)
        struct.pack_into("<I", header, 0, MAGIC)
        print("No header.bin found - creating fresh header")

    blocks = []
    for sec in cfg.sections():
        if not sec.startswith("Block"):
            continue
        idx = int(sec.replace("Block", ""))
        name = cfg[sec]["name"]
        lmode = int(cfg[sec]["lmode"])
        address = int(cfg[sec]["address"], 16)
        fname = cfg[sec]["file"]
        fpath = os.path.join(in_dir, fname)
        if not os.path.exists(fpath):
            print(f"ERROR: {fpath} not found!")
            return False
        fdata = open(fpath, "rb").read()
        blocks.append({
            "idx": idx,
            "name": name,
            "lmode": lmode,
            "address": address,
            "data": fdata,
            "size": len(fdata),
        })
        print(f"  Block{idx} ({name}): {len(fdata)} bytes from {fname}")

    blocks.sort(key=lambda x: x["idx"])

    cur_offset = HEADER_SIZE
    for b in blocks:
        b["offset"] = cur_offset
        cur_offset += b["size"]

    for b in blocks:
        desc_off = BLOCK_DESC_OFF + b["idx"] * BLOCK_DESC_SZ
        struct.pack_into("<IIII", header, desc_off,
            b["lmode"], b["size"], b["address"], b["offset"])
        print(f"  Block{b['idx']} descriptor: lmode={b['lmode']} size=0x{b['size']:X} addr=0x{b['address']:08X} offset=0x{b['offset']:X}")

    out_data = bytes(header)
    for b in blocks:
        out_data += b["data"]

    open(output_file, "wb").write(out_data)
    print(f"\nPacked: {output_file} ({len(out_data)} bytes)")
    return True

def main():
    import argparse
    p = argparse.ArgumentParser(description="Balong USB Loader Packer/Unpacker")
    p.add_argument("-u", metavar="FILE", help="Unpack USB loader file")
    p.add_argument("-p", metavar="DIR", help="Pack USB loader from directory")
    p.add_argument("-o", metavar="FILE", help="Output file (for pack mode)")
    p.add_argument("-d", metavar="DIR", help="Output directory (for unpack mode)")
    p.add_argument("--info", metavar="FILE", help="Show loader info without unpacking")
    p.add_argument("--safe", metavar="FILE", help="Create safe loader from input file")
    p.add_argument("--verify", nargs=2, metavar=("ORIG", "REPACK"), help="Verify repack integrity")
    
    args = p.parse_args()
    
    if args.info:
        sys.exit(0 if show_info(args.info) else 1)
    elif args.safe:
        out_file = os.path.splitext(args.safe)[0] + "_safe.bin"
        sys.exit(0 if make_safe_loader(args.safe, out_file) else 1)
    elif args.verify:
        sys.exit(0 if verify_repack(args.verify[0], args.verify[1]) else 1)
    elif args.u:
        ok = unpack(args.u, args.d)
        sys.exit(0 if ok else 1)
    elif args.p:
        if not args.o:
            print("ERROR: -o output file required for pack mode")
            sys.exit(1)
        ok = pack(args.p, args.o)
        sys.exit(0 if ok else 1)
    else:
        p.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()