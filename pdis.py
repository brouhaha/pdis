#!/usr/bin/python3

# Disassembler for UCSD p-system
# Copyright 2016 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import collections
import itertools
import sys

nil = 0xfc00

image_addr = 0
image_len = 0
mem = [0] * 65536
memusage = [None] * 65536

optab     = { 0x00: ('sldc', 'literal', 0x00),
              0x01: ('sldc', 'literal', 0x01),
              0x02: ('sldc', 'literal', 0x02),
              0x03: ('sldc', 'literal', 0x03),
              0x04: ('sldc', 'literal', 0x04),
              0x05: ('sldc', 'literal', 0x05),
              0x06: ('sldc', 'literal', 0x06),
              0x07: ('sldc', 'literal', 0x07),
              0x08: ('sldc', 'literal', 0x08),
              0x09: ('sldc', 'literal', 0x09),
              0x0a: ('sldc', 'literal', 0x0a),
              0x0b: ('sldc', 'literal', 0x0b),
              0x0c: ('sldc', 'literal', 0x0c),
              0x0d: ('sldc', 'literal', 0x0d),
              0x0e: ('sldc', 'literal', 0x0e),
              0x0f: ('sldc', 'literal', 0x0f),
              0x10: ('sldc', 'literal', 0x10),
              0x11: ('sldc', 'literal', 0x11),
              0x12: ('sldc', 'literal', 0x12),
              0x13: ('sldc', 'literal', 0x13),
              0x14: ('sldc', 'literal', 0x14),
              0x15: ('sldc', 'literal', 0x15),
              0x16: ('sldc', 'literal', 0x16),
              0x17: ('sldc', 'literal', 0x17),
              0x18: ('sldc', 'literal', 0x18),
              0x19: ('sldc', 'literal', 0x19),
              0x1a: ('sldc', 'literal', 0x1a),
              0x1b: ('sldc', 'literal', 0x1b),
              0x1c: ('sldc', 'literal', 0x1c),
              0x1d: ('sldc', 'literal', 0x1d),
              0x1e: ('sldc', 'literal', 0x1e),
              0x1f: ('sldc', 'literal', 0x1f),
              0x20: ('sldl', 'local', 0x01),
              0x21: ('sldl', 'local', 0x02),
              0x22: ('sldl', 'local', 0x03),
              0x23: ('sldl', 'local', 0x04),
              0x24: ('sldl', 'local', 0x05),
              0x25: ('sldl', 'local', 0x06),
              0x26: ('sldl', 'local', 0x07),
              0x27: ('sldl', 'local', 0x08),
              0x28: ('sldl', 'local', 0x09),
              0x29: ('sldl', 'local', 0x0a),
              0x2a: ('sldl', 'local', 0x0b),
              0x2b: ('sldl', 'local', 0x0c),
              0x2c: ('sldl', 'local', 0x0d),
              0x2d: ('sldl', 'local', 0x0e),
              0x2e: ('sldl', 'local', 0x0f),
              0x2f: ('sldl', 'local', 0x10),
              0x30: ('sldo', 'global', 0x01),
              0x31: ('sldo', 'global', 0x02),
              0x32: ('sldo', 'global', 0x03),
              0x33: ('sldo', 'global', 0x04),
              0x34: ('sldo', 'global', 0x05),
              0x35: ('sldo', 'global', 0x06),
              0x36: ('sldo', 'global', 0x07),
              0x37: ('sldo', 'global', 0x08),
              0x38: ('sldo', 'global', 0x09),
              0x39: ('sldo', 'global', 0x0a),
              0x3a: ('sldo', 'global', 0x0b),
              0x3b: ('sldo', 'global', 0x0c),
              0x3c: ('sldo', 'global', 0x0d),
              0x3d: ('sldo', 'global', 0x0e),
              0x3e: ('sldo', 'global', 0x0f),
              0x3f: ('sldo', 'global', 0x10),

              0x78: ('sind', 'literal', 0x00),
              0x79: ('sind', 'literal', 0x01),
              0x7a: ('sind', 'literal', 0x02),
              0x7b: ('sind', 'literal', 0x03),
              0x7c: ('sind', 'literal', 0x04),
              0x7d: ('sind', 'literal', 0x05),
              0x7e: ('sind', 'literal', 0x06),
              0x7f: ('sind', 'literal', 0x07),

              0x80: ('ldcb', 'literal', 'ub'),
              0x81: ('ldci', 'literal', 'w'),
              0x82: ('lca',  'const', 'b'),
              0x83: ('ldc',  'const', 'b', 'literal', 'ub'),
              0x84: ('lla',  'local', 'b'),
              0x85: ('ldo',  'global', 'b'),
              0x86: ('lao',  'global', 'b'),
              0x87: ('ldl',  'local', 'b'),
              0x88: ('lda',  'intermediate', 'db', 'b'),
              0x89: ('lod',  'intermediate', 'db', 'b'),
              0x8a: ('ujp',  'code', 'sb'),
              0x8b: ('ujpl', 'code', 'w'),
              0x8c: ('mpi',),
              0x8d: ('dvi',),
              0x8e: ('stm',  'literal', 'ub'),
              0x8f: ('modi',),

              0x90: ('cpl',  'local', 'proc', 'ub'),
              0x91: ('cpg',  'global', 'proc', 'ub'),
              0x92: ('cpi',  'intermediate', 'db', 'proc',  'ub'),
              0x93: ('cxl',  'segment', 'ub', 'local', 'proc', 'ub'),
              0x94: ('cxg',  'segment', 'ub', 'global', 'proc', 'ub'),
              0x95: ('cxi',  'segment', 'ub', 'intermediate', 'db', 'proc', 'ub'),
              0x96: ('rpu',  'literal', 'b'),
              0x97: ('cpf',),
              0x98: ('ldcn',),
              0x99: ('lsl',  'literal', 'db'),
              0x9a: ('lde',  'segment', 'ub', 'literal', 'b'),
              0x9b: ('lae',  'segment', 'ub', 'literal', 'b'),
              0x9c: ('nop',),
              0x9d: ('lpr',),
              0x9e: ('bpt',),
              0x9f: ('bnot',),

              0xa0: ('lor',),
              0xa1: ('land',),
              0xa2: ('adi',),
              0xa3: ('sbi',),
              0xa4: ('stl', 'local', 'b'),
              0xa5: ('sro', 'global', 'b'),
              0xa6: ('str', 'intermediate', 'db', 'b'),
              0xa7: ('ldb',),

              0xb0: ('equi',),
              0xb1: ('neqi',),
              0xb2: ('leqi',),
              0xb3: ('geqi',),
              0xb4: ('leusw',),
              0xb5: ('geusw',),
              0xb6: ('equpwr',),
              0xb7: ('leqpwr',),
              0xb8: ('geqpwr',),
              0xb9: ('equbyt',),
              0xba: ('leqbyt',),
              0xbb: ('geqbyt',),
              0xbc: ('srs',),
              0xbd: ('swap',),
              0xbe: ('tnc',),
              0xbf: ('rnd',),

              0xc0: ('adr',),
              0xc1: ('sbr',),
              0xc2: ('mpr',),
              0xc3: ('dvr',),
              0xc4: ('sto',),
              0xc5: ('mov', 'literal', 'b'),
              0xc6: ('dup2',),
              0xc7: ('adj', 'literal', 'ub'),
              0xc8: ('stb',),
              0xc9: ('ldp',),
              0xca: ('stp',),
              0xcb: ('chk',),
              0xcc: ('flt',),
              0xcd: ('equreal',),
              0xce: ('leqreal',),
              0xcf: ('geqreal',),

              0xd0: ('ldm', 'literal', 'ub'),
              0xd1: ('spr',),
              0xd2: ('efj', 'code', 'sb'),
              0xd3: ('nfj', 'code', 'sb'),
              0xd4: ('fjp', 'code', 'sb'),
              0xd5: ('fjpl', 'code', 'w'),
              0xd6: ('xjp', 'const', 'b'),
              0xd7: ('ixa', 'literal', 'b'),
              0xd8: ('ixp', 'literal', 'ub', 'literal', 'ub'),
              0xd9: ('ste', 'segment', 'ub', 'literal', 'b'),
              0xda: ('inn',),
              0xdb: ('uni',),
              0xdc: ('int',),
              0xdd: ('dif',),
              0xde: ('signal',),
              0xdf: ('wait',),

              0xe0: ('abi',),
              0xe1: ('ngi',),
              0xe2: ('dup1',),
              0xe3: ('abr',),
              0xe4: ('ngr',),
              0xe5: ('lnot',),
              0xe6: ('ind', 'literal', 'b'),
              0xe7: ('inc', 'literal', 'b')
              }
    
def read_rom(f):
    global image_addr, image_len, mem
    image_addr = 0xf400
    image_len = 0
    bytes = f.read(2)
    while bytes:
        mem[image_addr + image_len] = (bytes[1] << 8) + bytes[0]
        image_len += 1
        bytes = f.read(2)

def get_word(addr, name, file = None):
    w = mem[addr]
    if file is not None:
        print("%04x:  %04x  %s" % (addr, w, name), file = file)
    return w

def get_byte(addr, name, high, file = None):
    w = mem[addr]
    if high:
        b = w >> 8
    else:
        b = w & 0xff
    if file is not None:
        print("%04x%s: %02x    %s" % (addr, "LH"[int(high)], b, name), file = file)
    return b

def get_byte_offset_addr_str(segbase, segname, byte_offset, procname):
    addr = segbase + (byte_offset >> 1)
    high = (byte_offset & 1) != 0
    return "%04x%s %s+%04x %s" % (addr, "LH"[int(high)],
                                   segname, byte_offset,
                                   procname)

def get_byte_offset(segbase, segname, byte_offset, procname, file = None):
    addr = segbase + (byte_offset >> 1)
    high = (byte_offset & 1) != 0
    w = mem[addr]
    if high:
        b = w >> 8
    else:
        b = w & 0xff
    if file is not None:
        print("%s: %02x" % (get_byte_offset_addr_str(segbase, segname,
                                                     byte_offset, procname),
                            b),
              file = file)
    return b



def dis_boot_param_pointer(addr, name, file = None):
    if memusage[addr] is None:
        memusage[addr] = ['boot_param_pointer', 1]
    else:
        assert memusage[addr][0] == 'boot_param_pointer'

    return get_word(addr, name, file)

BootParams = collections.namedtuple('BootParams', ['ctp', 'sdp', 'rqp'])

def dis_boot_params(addr, name, file = None):
    if memusage[addr] is None:
        memusage[addr] = ['boot_params', 3]
    else:
        assert memusage[addr][0] == 'boot_params'
    
    ctp = get_word(addr + 0, name + '.ctp', file)
    sdp = get_word(addr + 1, name + '.sdp', file)
    rqp = get_word(addr + 2, name + '.rqp', file)
    return BootParams(ctp = ctp, sdp = sdp, rqp = rqp)
    
TIB = collections.namedtuple('TIB', ['waitq',
                                     'prior',
                                     'flags',
                                     'splow',
                                     'spupr',
                                     'sp',
                                     'mp',
                                     'bp',
                                     'ipc',
                                     'segb',
                                     'hangp',
                                     'iorslt',
                                     'sibsvec'])

def dis_tib(addr, name, file = None):
    if memusage[addr] is None:
        memusage[addr] = ['tib', 12]
    else:
        assert memusage[addr][0] == 'tib'
    
    waitq   = get_word(addr +  0, name + '.waitq',        file)
    prior   = get_byte(addr +  1, name + '.prior', False, file)
    flags   = get_byte(addr +  1, name + '.flags', False, file)
    splow   = get_word(addr +  2, name + '.splow',        file)
    spupr   = get_word(addr +  3, name + '.spupr',        file)
    sp      = get_word(addr +  4, name + '.sp',           file)
    mp      = get_word(addr +  5, name + '.mp',           file)
    bp      = get_word(addr +  6, name + '.bp',           file)
    ipc     = get_word(addr +  7, name + '.ipc',          file)
    segb    = get_word(addr +  8, name + '.segb',         file)
    hangp   = get_word(addr +  9, name + '.hangp',        file)
    iorslt  = get_word(addr + 10, name + '.iorslt',       file)
    sibsvec = get_word(addr + 11, name + '.sibsvec',      file)
    return TIB(waitq   = waitq,
               prior   = prior,
               flags   = flags,
               splow   = splow,
               spupr   = spupr,
               sp      = sp,
               mp      = mp,
               bp      = bp,
               ipc     = ipc,
               segb    = segb,
               hangp   = hangp,
               iorslt  = iorslt,
               sibsvec = sibsvec)

def dis_sibsvec(addr, count, name, file = None):
    if memusage[addr] is None:
        memusage[addr] = ['sibsvec', count]
    else:
        assert memusage[addr][0] == 'sibsvec'
    
    sibsvec = [0] * count
    for i in range(count):
        sibsvec[i] = get_word(addr + i, name + '[%d]' % i, file)
    return sibsvec

SIB = collections.namedtuple('SIB', ['segbase',
                                     'segleng',
                                     'segrefs',
                                     'segaddr',
                                     'segunit',
                                     'prevsp'])

def dis_sib(addr, name, file = None):
    if memusage[addr] is None:
        memusage[addr] = ['sib', 6]
    else:
        assert memusage[addr][0] == 'sib'
    
    segbase = get_word(addr + 0, name + '.segbase', file)
    segleng = get_word(addr + 1, name + '.segleng', file)
    segrefs = get_word(addr + 2, name + '.segrefs', file)
    segaddr = get_word(addr + 3, name + '.segaddr', file)
    segunit = get_word(addr + 4, name + '.segunit', file)
    prevsp  = get_word(addr + 5, name + '.prevsp',  file)
    return SIB(segbase = segbase,
               segleng = segleng,
               segrefs = segrefs,
               segaddr = segaddr,
               segunit = segunit,
               prevsp  = prevsp)

def dis_inst(segnum, segbase, segname, procname, byte_offset, file = None):
    ibytes = [get_byte_offset(segbase, segname, byte_offset, procname, None)]

    inst = list(optab.get(ibytes[0], ('undefined')))
    mnem = inst[0]
    s = "%-8s" % mnem
    flags = { 'literal':      False,
              'local':        False,
              'global':       False,
              'intermediate': False,
              'const':        False,
              'relative':     False,
              'proc':         False,
              'segment':      False,
              'code':         False }
    have_parm = False
    for i in range(1, len(inst)):
        if inst[i] in flags:
            flags[inst[i]] = True
        elif inst[i] == 'b':
            ibytes.append(get_byte_offset(segbase, segname, byte_offset + len(ibytes), procname, file = None))
            parm = ibytes[len(ibytes)-1]
            parm_size = 8
            if (parm >= 128):
                ibytes.append(get_byte_offset(segbase, segname, byte_offset + len(ibytes), procname, file = None))
                parm = ((parm - 128) << 8) + ibytes[len(ibytes)-1]
                parm_size = 16
            have_parm = True
        elif inst[i] == 'w':
            ibytes.append(get_byte_offset(segbase, segname, byte_offset + len(ibytes), procname, file = None))
            ibytes.append(get_byte_offset(segbase, segname, byte_offset + len(ibytes), procname, file = None))
            parm = (ibytes[len(ibytes)-1] << 8) + ibytes[len(ibytes)-2]
            if (parm >= 32768):
                parm -= 65536
            parm_size = 16
            have_parm = True
        elif inst[i] == 'ub' or inst[i] == 'db':
            ibytes.append(get_byte_offset(segbase, segname, byte_offset + len(ibytes), procname, file = None))
            parm = ibytes[len(ibytes)-1]
            parm_size = 8
            have_parm = True
        elif inst[i] == 'sb':
            ibytes.append(get_byte_offset(segbase, segname, byte_offset + len(ibytes), procname, file = None))
            parm = ibytes[len(ibytes)-1]
            if parm >= 128:
                parm -= 256
            parm_size = 8
            have_parm = True
        elif type(inst[i]) == int:
            parm = inst[i]
            parm_size = 8
            have_parm = True
        else:
            raise Exception("invalid entry in opcode table: " + str(inst[i]))
        if have_parm:
            # XXX here is where we should handle flags
            if flags['segment']:
                s = s + ' seg%d' % parm
            elif flags['code']:
                t = byte_offset + len(ibytes) + parm
                s = s + ' %s+%04x' % (segname, t)
            elif flags['intermediate']:
                s = s + ' intermediate %d' % parm
            elif flags['proc']:
                if flags['global']:
                    s = s + ' global proc%d' % parm
                elif flags['local']:
                    s = s + ' lproc%d' % parm
                else:
                    s = s + ' proc%d' % parm
            elif flags['global']:
                s = s + ' global_%d' % parm
            elif flags['local']:
                s = s + ' local_%d' % parm
            else:
                s = s + ' %d' % parm
            have_parm = 0
            for k in flags:
                flags[k] = False

    if file is not None:
        print("%s:" % get_byte_offset_addr_str(segbase, segname, byte_offset, procname),
              end = '', file = file)
        for i in range(4):
            if i < len(ibytes):
                print(" %02x" % ibytes[i], end = '', file = file)
            else:
                print("   ", end = '', file = file)
        print(" %s" % s, file = file)

    return len(ibytes)

def dis_proc(segnum, segbase, segname, procname, proc_offset, file = None):
    end_offset = get_word(segbase + proc_offset - 1, procname + '.endoffset', file)
    local_size = get_word(segbase + proc_offset + 0, procname + '.localsize', file)
    byte_offset = proc_offset * 2 + 2
    while byte_offset <= end_offset:
        byte_offset += dis_inst(segnum, segbase, segname,
                                procname, byte_offset, file = file)
    if file is not None and byte_offset & 1:
        get_byte_offset(segbase, segname, byte_offset, procname, file = file)

def dis_seg(segnum, segbase, seglength, segname, file = None):
    if memusage[segbase] is None:
        memusage[segbase] = ['segment', seglength, segnum, segname]
    else:
        assert memusage[segbase][0] == 'segment'
    
    proc_dir_offset = get_word(segbase, segname + '.procdir', file = file)
    if file is not None:
        print(file = file)

    if proc_dir_offset != seglength - 1:
        print('segment length %04x, proc dir offset %04x' % (seglength, proc_dir_offset), file = file)
    proc_dir = segbase + proc_dir_offset
    seg_num = get_byte(proc_dir + 0, segname + '.segnum', False, file = file)
    num_proc = get_byte(proc_dir + 0, segname + '.numproc', True, file = file)
    proc_offset = [0] * (num_proc + 1)
    for i in range(num_proc, 0, -1):
        proc_offset[i] = get_word(proc_dir - i, segname + '.proc%d_offset' % i, file = file)

    proc_by_offset = {}
    for i in range(1, num_proc + 1):
        proc_by_offset[proc_offset[i]] = i

    for po in sorted(proc_by_offset.keys()):
        p = proc_by_offset[po]
        dis_proc(segnum, segbase, segname, 'proc%d' % p, po, file)
        if file is not None:
            print(file = file)

    for i in range(num_proc, 0, -1):
        get_word(proc_dir - i, segname + '.proc%d_offset' % i, file)
    get_byte(proc_dir + 0, segname + '.segnum', False, file)
    get_byte(proc_dir + 0, segname + '.numproc', True, file)
    if file is not None:
        print(file = file)

def pass1_rom():
    boot_param_addr = dis_boot_param_pointer(image_addr, 'boot', file = None)

    boot_params = dis_boot_params(boot_param_addr, 'boot', file = None)

    tib = dis_tib(boot_params.ctp, 'tib', file = None)

    # XXX should determine segment count automatically, rather than
    # assume 2.
    sys_seg = dis_sibsvec(boot_params.sdp, 2, 'sdp', file = None)

    for i in range(len(sys_seg)):
        if sys_seg[i] != 0 and sys_seg[i] != nil:
            sib = dis_sib(sys_seg[i], 'sib%d' % i, file = None)
            dis_seg(i, sib.segbase, sib.segleng, 'seg%d' % i, file = None)


def pass2_rom(file, base, length):
    addr = base
    while addr < base + length:
        usage = memusage[addr]
        if usage is None:
            get_word(addr, '', file = file)
            usage = (None, 1)
        elif usage[0] == 'boot_param_pointer':
            dis_boot_param_pointer(addr, 'boot', file = file)
        elif usage[0] == 'boot_params':
            dis_boot_params(addr, 'boot', file = file)
        elif usage[0] == 'tib':
            dis_tib(addr, 'tib', file = file)
        elif usage[0] == 'sibsvec':
            dis_sibsvec(addr, 2, 'sdp', file = file)
        elif usage[0] == 'sib':
            dis_sib(addr, 'sib', file = file)
        elif usage[0] == 'segment':
            dis_seg(segnum    = usage[2],
                    segbase   = addr,
                    seglength = usage[1],
                    segname   = usage[3],
                    file = file)
        else:
            raise Exception("invalid memory usage entry " + str(usage))
        print(file = file)
        addr += usage[1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('objectfile', type=argparse.FileType('rb'))
    parser.add_argument('disfile', type=argparse.FileType('w'), nargs='?', default = sys.stdout)
    args = parser.parse_args()

    read_rom(args.objectfile)
    args.objectfile.close()

    pass1_rom()

    if args.disfile is not None:
        pass2_rom(args.disfile, 0xf400, 0x200)

