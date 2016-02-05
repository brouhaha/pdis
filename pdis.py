#!/usr/bin/python3

# Disassembler for UCSD p-system release III.0, as used by the
# Western Digital WD9000 Pascal Microengine chipset
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

#from pyImageDisk import disk, filesystem

nil = 0xfc00

image_base = 0
image_len = 0
mem = None
memusage = None
labels = None

def mem_init():
    global image_base, image_len, mem, memusage, labels
    image_base = 0
    image_len = 0
    mem = [0] * 65536
    memusage = [None] * 65536
    labels = [None] * 131072

def add_label(seg_base, byte_offset, label):
    global labels
    labels[seg_base * 2 + byte_offset] = label


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
              0xd6: ('xjp', 'case', 'b'),
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
    
def read_words(f, count):
    global image_base, image_len, mem
    image_base = 0
    image_len = 0
    while count:
        bytes = f.read(2)
        mem[image_base + image_len] = (bytes[1] << 8) + bytes[0]
        image_len += 1
        count -= 1
    
def read_image(f, base):
    global image_base, image_len, mem
    image_base = base
    image_len = 0
    bytes = f.read(2)
    while bytes:
        mem[image_base + image_len] = (bytes[1] << 8) + bytes[0]
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

def get_byte_offset_addr_str(seg_base, seg_name, byte_offset, proc_name):
    addr = seg_base + (byte_offset >> 1)
    high = (byte_offset & 1) != 0
    return "%04x%s %s+%04x %s" % (addr, "LH"[int(high)],
                                   seg_name, byte_offset,
                                   proc_name)

def get_byte_offset(seg_base, seg_name, byte_offset, proc_name, file = None):
    addr = seg_base + (byte_offset >> 1)
    high = (byte_offset & 1) != 0
    w = mem[addr]
    if high:
        b = w >> 8
    else:
        b = w & 0xff
    if file is not None:
        print("%s: %02x" % (get_byte_offset_addr_str(seg_base, seg_name,
                                                     byte_offset, proc_name),
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
        count = memusage[addr][1]
    
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

# AOS track 0 bootstrap seems to only use a three-word SIB entry
def dis_sib(addr, name, short = False, file = None):
    if memusage[addr] is None:
        memusage[addr] = ['sib', 3 if short else 6]
    else:
        assert memusage[addr][0] == 'sib'
        short = memusage[addr][1] == 3
    
    segbase = get_word(addr + 0, name + '.segbase', file)
    segleng = get_word(addr + 1, name + '.segleng', file)
    if not short:
        segrefs = get_word(addr + 2, name + '.segrefs', file)
        segaddr = get_word(addr + 3, name + '.segaddr', file)
        segunit = get_word(addr + 4, name + '.segunit', file)
        prevsp  = get_word(addr + 5, name + '.prevsp',  file)
    else:
        unknown = get_word(addr + 2, name + '.segunk', file)
        segrefs = None
        segaddr = None
        segunit = None
        prevsp  = None
    return SIB(segbase = segbase,
               segleng = segleng,
               segrefs = segrefs,
               segaddr = segaddr,
               segunit = segunit,
               prevsp  = prevsp)

def dis_case(seg_base, seg_name, proc_name, table_offset, jump_offset, name, file = None):
    global next_label_num

    if memusage[seg_base + table_offset] is None:
        first = get_word(seg_base + table_offset + 0, name + '.min', file)
        last  = get_word(seg_base + table_offset + 1, name + '.max', file)
        count = last + 1 - first
        memusage[seg_base + table_offset] = ['case', count + 2, proc_name, jump_offset, name]
        print('%04x' % (seg_base + table_offset), memusage[seg_base + table_offset])
    else:
        assert memusage[seg_base + table_offset][0] == 'case'
        if proc_name is None:
            proc_name = memusage[seg_base + table_offset][2]
        if jump_offset is None:
            jump_offset = memusage[seg_base + table_offset][3]
        if name is None:
            name = memusage[seg_base + table_offset][4]
        first = get_word(seg_base + table_offset + 0, name + '.min', file)
        last  = get_word(seg_base + table_offset + 1, name + '.max', file)
        count = last + 1 - first

    offsets = [None] * count
    for i in range(count):
        t = get_word(seg_base + table_offset + 2 + i, name+'.idx%04x' % (first + i), file) + jump_offset
        offsets[i] = t
        if proc_name is not None:
            add_label(seg_base, t, '%s.%s.%02x' % (seg_name, proc_name, next_label_num))
            next_label_num += 1

def dis_inst(seg_num, seg_base, seg_name, proc_name, byte_offset, file = None):
    global next_label_num
    ibytes = [get_byte_offset(seg_base, seg_name, byte_offset, proc_name, None)]

    inst = list(optab.get(ibytes[0], ('undefined',)))
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
              'code':         False,
              'case':         False, }
    have_parm = False
    for i in range(1, len(inst)):
        if inst[i] in flags:
            flags[inst[i]] = True
        elif inst[i] == 'b':
            ibytes.append(get_byte_offset(seg_base, seg_name, byte_offset + len(ibytes), proc_name, file = None))
            parm = ibytes[len(ibytes)-1]
            parm_size = 8
            if (parm >= 128):
                ibytes.append(get_byte_offset(seg_base, seg_name, byte_offset + len(ibytes), proc_name, file = None))
                parm = ((parm - 128) << 8) + ibytes[len(ibytes)-1]
                parm_size = 16
            have_parm = True
        elif inst[i] == 'w':
            ibytes.append(get_byte_offset(seg_base, seg_name, byte_offset + len(ibytes), proc_name, file = None))
            ibytes.append(get_byte_offset(seg_base, seg_name, byte_offset + len(ibytes), proc_name, file = None))
            parm = (ibytes[len(ibytes)-1] << 8) + ibytes[len(ibytes)-2]
            if (parm >= 32768):
                parm -= 65536
            parm_size = 16
            have_parm = True
        elif inst[i] == 'ub' or inst[i] == 'db':
            ibytes.append(get_byte_offset(seg_base, seg_name, byte_offset + len(ibytes), proc_name, file = None))
            parm = ibytes[len(ibytes)-1]
            parm_size = 8
            have_parm = True
        elif inst[i] == 'sb':
            ibytes.append(get_byte_offset(seg_base, seg_name, byte_offset + len(ibytes), proc_name, file = None))
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
            if flags['case']:
                dis_case(seg_base, seg_name, proc_name, parm, byte_offset + len(ibytes), proc_name + '.case_%04x' % byte_offset, file = None)
            elif flags['segment']:
                s = s + ' seg%d' % parm
            elif flags['code']:
                t = byte_offset + len(ibytes) + parm
                s = s + ' %s+%04x' % (seg_name, t)
                add_label(seg_base, t, '%s.%s.%02x' % (seg_name, proc_name, next_label_num))
                next_label_num += 1
            elif flags['intermediate']:
                s = s + ' intermediate %d' % parm
            elif flags['proc']:
                if flags['global']:
                    s = s + ' global proc%d' % parm
                elif flags['local']:
                    s = s + ' local proc%d' % parm
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
        print("%s:" % get_byte_offset_addr_str(seg_base, seg_name, byte_offset, proc_name),
              end = '', file = file)
        for i in range(4):
            if i < len(ibytes):
                print(" %02x" % ibytes[i], end = '', file = file)
            else:
                print("   ", end = '', file = file)
        label = labels[seg_base * 2 + byte_offset]
        if label is not None:
            print("%-19s " % (label + ':'), end = '', file = file)
        else:
            print("                    ", end = '', file = file)
        print("%s" % s, file = file)

    return len(ibytes)

def dis_proc(seg_num, seg_base, seg_name, proc_name, proc_offset, end_offset = None, file = None):
    global next_label_num
    next_label_num = 0
    if end_offset is None:
        end_offset = get_word(seg_base + proc_offset - 1, proc_name + '.endoffset', file)
    local_size = get_word(seg_base + proc_offset + 0, proc_name + '.localsize', file)
    byte_offset = proc_offset * 2 + 2
    while byte_offset <= end_offset:
        byte_offset += dis_inst(seg_num, seg_base, seg_name,
                                proc_name, byte_offset, file = file)
    if file is not None and byte_offset & 1:
        get_byte_offset(seg_base, seg_name, byte_offset, proc_name, file = file)
        byte_offset += 1
    return (byte_offset // 2) - (proc_offset - 1)

def dis_seg_nonproc(seg_num, seg_base, seg_name, word_offset, file = None):
    usage = memusage[seg_base + word_offset]
    if (usage is not None) and (usage[0] == 'case'):
        dis_case(seg_base, seg_name, None, word_offset, None, None, file = file)
    else:
        get_word(seg_base + word_offset, '', file = file)
    return 1

def dis_seg(seg_num, seg_base, seg_length, seg_name, file = None):
    if memusage[seg_base] is None:
        memusage[seg_base] = ['segment', seg_length, seg_num, seg_name]
    else:
        assert memusage[seg_base][0] == 'segment'
    
    proc_dir_offset = get_word(seg_base, seg_name + '.procdir', file = file)
    if file is not None:
        print(file = file)

    if proc_dir_offset != seg_length - 1:
        print('segment length %04x, proc dir offset %04x' % (seg_length, proc_dir_offset), file = file)
    proc_dir = seg_base + proc_dir_offset
    seg_num = get_byte(proc_dir + 0, seg_name + '.segnum', False, file = None)
    num_proc = get_byte(proc_dir + 0, seg_name + '.numproc', True, file = None)
    proc_offset = [0] * (num_proc + 1)
    for i in range(num_proc, 0, -1):
        proc_offset[i] = get_word(proc_dir - i, seg_name + '.proc%d_offset' % i, file = None)

    proc_by_offset = {}
    for i in range(1, num_proc + 1):
        proc_by_offset[proc_offset[i]] = i

    next_offset = 1
    for po in sorted(proc_by_offset.keys()):
        p = proc_by_offset[po]
        #print("po %04x, next_offset %04x" % (po, next_offset), file = file)
        while (po - 1) > next_offset:
            #print("other at offset %04x" % next_offset, file = file)
            next_offset += dis_seg_nonproc(seg_num, seg_base, seg_name, next_offset, file = file)
        else:
            next_offset += dis_proc(seg_num, seg_base, seg_name, 'proc%d' % p, po, file = file)
        if file is not None:
            print(file = file)
    while next_offset < seg_length:
        #print("other at offset %04x" % next_offset, file = file)
        next_offset += dis_seg_nonproc(seg_num, seg_base, seg_name, next_offset, file)

    if file is not None:
        for i in range(num_proc, 0, -1):
            get_word(proc_dir - i, seg_name + '.proc%d_offset' % i, file)
        get_byte(proc_dir + 0, seg_name + '.segnum', False, file = file)
        get_byte(proc_dir + 0, seg_name + '.numproc', True, file = file)
        print(file = file)

def pass_1_rom(seg_count):
    boot_param_addr = dis_boot_param_pointer(image_base, 'boot', file = None)

    boot_params = dis_boot_params(boot_param_addr, 'boot', file = None)
    ctp_addr = boot_params.ctp

    tib = dis_tib(ctp_addr, 'tib', file = None)

    sys_seg = dis_sibsvec(boot_params.sdp, seg_count, 'sdp', file = None)

    for i in range(len(sys_seg)):
        if sys_seg[i] != 0 and sys_seg[i] != nil:
            sib = dis_sib(sys_seg[i], 'sib%d' % i, file = None)
            if sib.segbase != 0 and sib.segbase != nil:
                dis_seg(i, sib.segbase, sib.segleng, 'seg%d' % i, file = None)
        
def pass_1_wdboot(seg_count):
    boot_param_addr = 0

    boot_params = dis_boot_params(boot_param_addr, 'boot', file = None)
    ctp_addr = boot_params.ctp

    tib = dis_tib(ctp_addr, 'tib', file = None)

    sys_seg = dis_sibsvec(boot_params.sdp, seg_count, 'sdp', file = None)

    for i in range(len(sys_seg)):
        if sys_seg[i] != 0 and sys_seg[i] != nil:
            sib = dis_sib(sys_seg[i], 'sib%d' % i, file = None)
            if sib.segbase != 0 and sib.segbase != nil:
                dis_seg(i, sib.segbase, sib.segleng, 'seg%d' % i, file = None)
        
def pass_1_acdboot(seg_count):
    ctp_addr = 0x2000
    seg_base = 0x200c
    seg_length = mem[seg_base] + 1

    tib = dis_tib(ctp_addr, 'tib', file = None)

    dis_seg(1, seg_base, seg_length, 'boot', file = None)
        

def pass_2(file):
    global image_base, image_len
    addr = image_base
    while addr < image_base + image_len:
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
            dis_seg(seg_num    = usage[2],
                    seg_base   = addr,
                    seg_length = usage[1],
                    seg_name   = usage[3],
                    file = file)
        else:
            raise Exception("invalid memory usage entry " + str(usage))
        print(file = file)
        addr += usage[1]


def get8(b, offset):
    return b[offset]

def get16(b, offset):
    return b[offset] + (b[offset+1] << 8)

def getalpha(b, offset):
    a = ''
    for i in range(8):
        a += chr(b[offset + i])
    return a


SegInfo = collections.namedtuple('SegInfo', ['block',
                                             'length',
                                             'name',
                                             'kind',
                                             'addr',
                                             'segnum',
                                             'codeversion'])

def get_code_seg_info(seg_page, rel_seg_num):
    block = get16(seg_page, rel_seg_num * 4)
    length = get16(seg_page, rel_seg_num * 4 + 2)
    name = getalpha(seg_page, 0x040 + rel_seg_num * 8)
    kind = get16(seg_page, 0x0c0 + rel_seg_num * 2)
    addr = get16(seg_page, 0x0e0 + rel_seg_num * 2)
    segnum = get8(seg_page, 0x100 + rel_seg_num * 2)
    codeversion = get8(seg_page, 0x100 + rel_seg_num * 2 + 1)
    return SegInfo(block  = block,
                   length = length,
                   name   = name,
                   kind   = kind,
                   addr   = addr,
                   segnum = rel_seg_num,
                   codeversion = codeversion)
    
BlockInfo = collections.namedtuple('BlockInfo', ['block',
                                                 'block_count',
                                                 'kind',
                                                 'what', # 'code', 'interface'
                                                 'seg_info'])

# AOS uses an entirely different code file header
# first two bytes of first block are always 0xffff
# next two bytes are block number of next index block, or 0x0000
def dis_aos_codefile(cf, header, df):
    pass  # XXX more code needed here (obviously)
    

# III.0 uses a code file header similar to II.0
def dis_ucsd_codefile(cf, header, df):
    verbose = False
    # traditional p-System code file header
    seg_info = [get_code_seg_info(header, i) for i in range(16)]

    # XXX Support for vectored code files (which can have segments 0..15 for
    # system, or 128..143 for user, has not been tested.
    code_kind = ['static', 'vectored'][header[0x16f]]
    if code_kind == 'vectored':
        last_seg = get16(header, 0x170)
        last_code_block = get16(header, 0x172)
        orig_f_pos = cf.tell()
        cf.seek((last_code_block + 1) * 512)
        for i in range(16, lastseg, 16):
            seg_page = cf.read(512)
            seg_info.append([get_code_seg_info(header, i) for i in range(16)])
        cf.seek(orig_f_pos)

    block_info = {}

    for i in range(len(seg_info)):
        si = seg_info[i]
        if si.block != 0:
            if si.kind < 5:
                kind = ['linked', 'hostseg', 'segproc', 'unitseg', 'seprtseg'][si.kind]
            else:
                kind = str(si.kind)
            assert si.block not in block_info
            block_info[si.block] = BlockInfo(block = si.block,
                                             block_count = (si.length + 255) // 256,

                                             kind = kind,
                                             what = 'code',
                                             seg_info = si)
            if kind == 'unitseg':
                assert si.addr != 0
                assert si.addr not in block_info
                block_info[si.addr] = BlockInfo(block = si.addr,
                                                block_count = si.block - si.addr,
                                                kind = kind,
                                                what = 'interface',
                                                seg_info = si)

    print_seg_list = True
    if print_seg_list:
        print('       blk  leng name     kind     addr cver')
    sk = sorted(block_info.keys())
    for i in range(len(sk)):
        block = sk[i]
        bi = block_info[block]
        si = bi.seg_info
        if bi.what == 'interface':
            if print_seg_list:
                print('interface')
        elif bi.what == 'code':
            if print_seg_list:
                print('seg%02d: %04x %04x %s %-8s %04x %04x' % (si.segnum,
                                                                si.block,
                                                                si.length,
                                                                si.name,
                                                                bi.kind,
                                                                si.addr,
                                                                si.codeversion),
                      file = df)
    if verbose:
        print(file = df)

    expected_block = 1
    for i in range(len(sk)):
        block = sk[i]
        bi = block_info[block]
        si = bi.seg_info
        assert block >= expected_block
        if block > expected_block:
            count = block - expected_block
            print("skipping %d blocks of unknown content" % count)
            cf.read(512 * count)
            expected_block += count
            assert block == expected_block
        if bi.what == 'interface':
            print('%d blocks of interface text' % bi.block_count)
            cf.read(512 * bi.block_count)
        elif bi.what == 'code':
            seg_name = si.name.strip()
            if seg_name == '':
                seg_name = 'seg%d' % si.segnum
            mem_init()
            print("reading segment %s, file pos %04x" % (seg_name, cf.tell()))
            read_words(cf, bi.block_count * 256)
            dis_seg(si.segnum, 0, si.length, seg_name, None)
            pass_2(df)
        else:
            assert False

        expected_block += bi.block_count


def dis_codefile(cf, df):
    header = cf.read(512)
    if get16(header, 0) == 0xffff:
        dis_aos_codefile(cf, header, df)
    else:
        dis_ucsd_codefile(cf, header, df)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    input_file_type_group = parser.add_mutually_exclusive_group()
    input_file_type_group.add_argument('--acdboot', action='store_true', help='disassemble track 0 floppy bootstrap (loaded by ACD PDQ-3 boot ROM)')
    input_file_type_group.add_argument('--wdboot', action='store_true', help='disassemble track 0 and 1 floppy bootstrap (track 1 loaded by WD9000 microcode)')
    input_file_type_group.add_argument('--rom',  action='store_true', help='disassemble boot ROM')

#    parser.add_argument('--imd', nargs='?', type=argparse.FileType('rb'), help='get object file input from an ImageDisk image')
    parser.add_argument('--imd', nargs='?', help='get object file input from an ImageDisk image')

    parser.add_argument('objectfile', help = 'object file for input')

    parser.add_argument('disfile', type=argparse.FileType('w'), nargs='?', default = sys.stdout, help = 'disassembly output file')

    args = parser.parse_args()

    print(args)
    
    if args.imd is not None:
        #raise NotImplementedError('This is a stub for future development.')
        imd = disk.disk(filename = args.imd)
    else:
        objectfile = open(args.objectfile, 'rb')

    if args.rom or args.wdboot or args.acdboot:
        mem_init()

        if args.rom:
            base = 0xf400
            read_image(objectfile, base)
            objectfile.close()
            pass_1_rom(seg_count = 2)
        elif args.wdboot:
            base = 0x0000
            read_image(objectfile, base)
            objectfile.close()
            pass_1_wdboot(seg_count = 16)
        elif args.acdboot:
            base = 0x2000
            read_image(objectfile, base)
            print("image_base %04x, image_len %04x" % (image_base, image_len))
            objectfile.close()
            pass_1_acdboot(seg_count = 2)

        if args.disfile is not None:
            pass_2(args.disfile)
            args.disfile.close()
    else:
        dis_codefile(objectfile, args.disfile)
        objectfile.close()
        args.disfile.close()
