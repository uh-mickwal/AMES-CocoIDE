#!/usr/bin/env python3
# CdM8 assembler

# V1 (c) Prof. Alex Shaferenko.  July 2015
# V1.1. Some modifications by M L Walters, August/Sept 2015
# V2 Adapted for cocideV0.8 Oct 2016
# V2.3: Error message bug fixed for cocoideV0.9
# V2.4: Macro compile bug fixed for CocoIDEV0.992
# V2.5: A Shaferenko, NewCocas.
# V2.6: M Walters, Jan 2020, rol replaced by swan instruction (mark 5 core)
# V2.7: M Walters, Added GUI


# Python 2 and 3 compatibility
from __future__ import absolute_import, division, print_function
from typing import Any, Optional, Tuple, Union, List, Dict

try:
    input = raw_input  # type: ignore # Python 3 style input()
except:
    pass


ASM_VER = "2.7"

import os, sys
import time
import argparse
import io

try:
    # Python 3 tk
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    from tkinter import messagebox
    from tkinter import scrolledtext as sctx
    import tkinter.font as font

except:
    # Python 2 tk (runs but not exhaustively tested!)
    # Ames lib (sendfile.py) not python 2 compatible (urllib)
    import Tkinter as tk  # type: ignore
    import ttk  # type: ignore
    import tkFileDialog as filedialog  # type: ignore
    import tkMessageBox as messagebox  # type: ignore
    import ScrolledText as sctx  # type: ignore
    import tkFont as font  # type: ignore

###################### C D M 8  A S S E M B L E R  Facilities
#


class Context:
    def __init__(self, cdm8ver=4):  # type: (int) -> None
        if cdm8ver == 4:
            self.v3 = False
        else:
            self.v3 = True
        self.dbg = False
        self.save = False

        self.lst = False
        self.sym = None

        self.filename = None  # type: Optional[str]
        self.text = []  # type: List[str]
        self.counter = 0
        self.rel = False
        self.rel_list = {}  # type: Dict[str, List[int]]
        self.exts = {}  # type: Dict[str, List[Tuple[Optional[str], int]]]
        self.ents = {}  # type: Dict[str, Dict[str, int]]
        self.abses = {}  # type: Dict[str, int]
        self.labels = {}  # type: Dict[str, Dict[str, int]]
        self.rsects = {}  # type: Dict[str, int]
        self.sect_name = None  # type: Optional[str]
        self.labels["$abs"] = {}
        self.ents["$abs"] = {}
        self.tpls = {}  # type: Dict[str, Dict[str, int]]
        self.tpl = False
        self.ds_ins = False
        self.tpl_name = ""
        self.generated = []  # type: List[bool]
        self.got_minus = False
        self.lst_me = False  # flag: include macro expansions in listing
        # macro vars as well
        self.mcount = 1  # nonce for macros
        self.mcalls = 0  # the number of macro expansions made so far
        self.macdef = False
        self.mname = ""
        self.marity = 0
        self.mvars = {}  # type: Dict[str, str]
        self.macros = {}  # type: Dict[str, List[str]]
        self.mstack = [[], [], [], [], [], []]  # type: List[List[str]]
        self.pars = []  # type: List[str]


# Used by CocoIDE when imported
ret_error = False
error_msg = ""
err_line = None

# Instruction set
bi = 2  # binary arithmetic/logic & ld/st ops
un = 1  # unary arithmetic/logic & stack/immediate ops
zer = 0  # 0-addr commands
br = -1  # branches
spmove = -2  # stack setting and offsetting
bbne = -2  # branch back
osix = -3  # osix, extended OS interrupt
spec = -4  # special assembler instructions
mc = -5  # assembler macro/mend commands
mi = -6  # macro instruction

iset = {
    # binary
    "move": (0x00, bi),
    "add": (0x10, bi),
    "addc": (0x20, bi),
    "sub": (0x30, bi),
    "and": (0x40, bi),
    "or": (0x50, bi),
    "xor": (0x60, bi),
    "cmp": (0x70, bi),
    # unary
    "not": (0x80, un),
    "neg": (0x84, un),
    "dec": (0x88, un),
    "inc": (0x8C, un),
    "shr": (0x90, un),
    "shla": (0x94, un),
    "shra": (0x98, un),
    "swan": (0x9C, un),
    # memory
    "st": (0xA0, bi),
    "ld": (0xB0, bi),
    "ldc": (0xF0, bi),
    # stack
    "push": (0xC0, un),
    "pop": (0xC4, un),
    #    "stsp": (0xC8,un),  # mark 3 Architecture # Not needed as macro replacements done
    #    "ldsp": (0xCC,un),  # mark 3 Architecture
    "ldsa": (0xC8, un),  # mark 4 architecture
    "addsp": (0xCC, spmove),  # mark 4 architecture
    "setsp": (0xCD, spmove),  # mark 4 architecture
    "pushall": (0xCE, zer),  # mark 4 architecture
    "popall": (0xCF, zer),  # mark 4 architecture
    # load immediate
    "ldi": (0xD0, un),
    # clock control
    "halt": (0xD4, zer),
    "wait": (0xD5, zer),
    # immediate address
    "jsr": (0xD6, br),
    "rts": (0xD7, zer),
    #
    "ioi": (0xD8, zer),
    "rti": (0xD9, zer),
    "crc": (0xDA, zer),
    #    "osix": (0xDB,osix),
    # branches
    "beq": (0xE0, br),
    "bz": (0xE0, br),
    "bne": (0xE1, br),
    "bnz": (0xE1, br),
    "bhs": (0xE2, br),
    "bcs": (0xE2, br),
    "blo": (0xE3, br),
    "bcc": (0xE3, br),
    "bmi": (0xE4, br),
    "bpl": (0xE5, br),
    "bvs": (0xE6, br),
    "bvc": (0xE7, br),
    "bhi": (0xE8, br),
    "bls": (0xE9, br),
    "bge": (0xEA, br),
    "blt": (0xEB, br),
    "bgt": (0xEC, br),
    "ble": (0xED, br),
    "br": (0xEE, br),
    "noop": (0xEF, br),
    "lchk": (0, br),
    #
    # assembler commandsjust
    "asect": (0, spec),
    "rsect": (0, spec),
    "tplate": (0, spec),
    "ext": (0, spec),
    "ds": (0, spec),
    "dc": (0, spec),
    "set": (0, spec),
    #
    # macro facilities
    "macro": (0, mc),
    "mend": (0, mc),
    #
    "end": (0, spec),
}  # type: Dict[str, Tuple[int, int]]


class CocAs(tk.Tk):
    def __init__(self, master=None, name="cocas", exitroot=False, sym=True):
        self.master = master
        self.mainWin = tk.Toplevel(master=master)
        self.mainWin.lift()
        # self.mainWin.update()
        # self.mainWin.wm_attributes("-topmost", False)
        # self.mainWin.__init__()
        self.mainWin.resizable(width=False, height=False)  # width=False, height=False)
        self.mainWin.title("CDM8 Assembler: CocAs GUI")
        if __name__ == "__main__":
            self.mainWin.protocol(
                "WM_DELETE_WINDOW", self.closeCocas
            )  # Only if main module
        self.mainWin.focus()
        ## Create buttonbar, link and status panels
        buttonBar = tk.Frame(
            self.mainWin, name="buttonbar", height=35, width=400, border=2, pady=5
        )  # , bg="red")
        buttonBar.pack(side=tk.TOP, fill=tk.X, expand=False)

        linkPanel = tk.Frame(
            self.mainWin, name="link", border=2, relief="sunken", pady=5
        )  # , bg="white")
        linkPanel.pack(side=tk.TOP, fill=tk.X, expand=1)
        self.linkText = tk.Label(linkPanel, text="No file selected", height=2)
        self.linkText.pack(expand=1)
        self.linkText.bind("<Key>", lambda e: "break")

        seperator = tk.Frame(self.mainWin, name="sep1", height=35, border=2, pady=5)
        seperator.pack(side=tk.TOP, fill=tk.BOTH, expand=False)

        statusPanel = tk.Frame(
            self.mainWin, name="status", border=2, relief="sunken", pady=5, bg="white"
        )
        statusPanel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.statusText = sctx.ScrolledText(statusPanel, height=25, wrap=tk.NONE)
        self.statusText.pack(fill=tk.BOTH, expand=1)
        self.statusText.bind("<Key>", lambda e: "break")

        # self.linkText.config(state=tk.DISABLED)

        # buttons
        addButton = tk.Button(
            buttonBar, text="Select .asm File", command=self.addFile
        )  # , height=2)
        addButton.pack(side=tk.LEFT)
        # remButton = tk.Button(buttonBar, text="Remove\n OBJ File", command=self.remObjFile)#, height=2)
        # remButton.pack(side=tk.LEFT)
        linkButton = tk.Button(
            buttonBar,
            text="Assemble to .obj File",
            command=lambda: self.asmFile(sym=sym),
        )  # , height=2)
        linkButton.pack(side=tk.LEFT)
        # linkButton = tk.Button(buttonBar, text="Asse Logisim Image", command=self.linkFiles)#, height=2)
        # linkButton.pack(side=tk.LEFT)
        quitButton = tk.Button(
            buttonBar, text="Quit", command=self.closeCocas
        )  # , height=2)
        quitButton.pack(side=tk.LEFT)

        self.asmfile = ""

    def addFile(self, event=None):
        # print("add file")
        filepath = None

        try:
            filepath = filedialog.askopenfilename(
                filetypes=(("CDM8 Assembly File", "*.asm"), ("All files", "*.*"))
            )
        except:
            pass
        self.mainWin.lift()
        if filepath:
            self.asmfile = filepath
            # print(objfiles)
            # self.linkText.delete(1.0, tk.END)
            # for filepath in objfiles:
            # print(filepath)
            self.linkText.config(text=filepath + "\n")
            self.statusText.delete("1.0", tk.END)

    def asmFile(self, event=None, sym=False):
        global error_msg

        error_msg = ""

        ctx = Context()
        ctx.lst = True
        ctx.sym = sym

        self.statusText.delete("1.0", tk.END)
        if not self.asmfile:
            error_msg = "No file to Assemble!\n"
        else:
            if self.asmfile[-4:] == ".asm":
                filename = self.asmfile[:-4]
                try:
                    fileBuff = open(filename + ".asm", "r")
                except IOError:
                    error_msg = filename + ".asm: file not found"
        if not error_msg:
            try:
                ctx.filename = filename
                obj_code, codelist, error_msg = compile_asm(
                    fileBuff, ctx=ctx
                )  # , self.cdm8ver)
            except Exception as e:
                error_msg = str(e)
        if error_msg:
            self.statusText.insert(tk.END, error_msg)
        else:
            self.statusText.insert(
                tk.END,
                "\n\nASSEMBLED OK! Written to:\n " + self.asmfile[:-4] + ".obj\n",
            )
            self.statusText.insert(tk.END, "\nASSEMBLER REPORT LISTING:\n" + codelist)
            self.statusText.insert(tk.END, "\nOBJECT CODE:\n")
            self.statusText.insert(tk.END, obj_code)
            self.statusText.see(tk.END)
            # print("**", obj_code) # debug
        # Save obj file
        # print("Saving obj file")
        try:
            with io.open(filename + ".obj", "w", encoding="utf8") as f:
                f.write(obj_code)
            print()
        except TypeError:
            raise
            error_msg = "TypeError"
            # return "break"
        except Exception as e:
            # raise
            error_msg = str(e)
            # return "break"
        if error_msg:
            self.statusText.insert(tk.END, error_msg)
        else:
            self.statusText.insert(tk.END, "\nSaved OBJ:\n " + filename + ".obj OK")
        self.statusText.see(tk.END)

    def closeCocas(self):
        self.mainWin.destroy()
        if __name__ == "__main__":
            self.master.destroy()  # type: ignore


class LE(Exception):
    def __init__(self, i, m):
        global err_line
        # err_line = i
        # print("LE",i,m)#debug
        global ret_error, error_msg
        # print("**", retError)
        # if retError:
        #    error_msg = "LINE "+ str(i) +": "+m
        # else:
        error_msg = m
        # error_msg += "\n"+m
        self.ind = i
        self.msg = m


class SE(Exception):
    def __init__(self, ctx, i, m):
        global ret_error, error_msg
        # print("SE",i,m)#debug
        # if retError:
        #    error_msg = "LINE "+ str(i) +": "+m
        # else:
        if not ctx.macdef:
            error_msg = m
        # error_msg += "\n"+m
        self.ind = i
        self.msg = m


def lex(ctx, s):
    def hexbyte(s):
        w = s
        w = w.lower()
        k = "0123456789abcdef".find(w[0])
        m = "0123456789abcdef".find(w[1])
        if m < 0 or k < 0:
            return -1
        return 16 * k + m

    ln = len(s)
    if ln == 0:
        return ["emp", -1, 0]
    i = 0
    while s[i] == " " or s[i] == "\t" or s[i] == "#":
        if i == ln - 1 or s[i] == "#":
            return ["emp", -1, 0]
        else:
            i = i + 1
    x = s[i]
    if x.isalpha() or x == "_" or x == "*":
        CAT = "id"
    elif x.isdigit():
        CAT = "num"
    elif x in ":,+->/'?!.=":
        CAT = x
    elif x == '"':
        CAT = "str"
    elif x == "$":
        CAT = "par"
    else:
        raise LE(i, "Illegal character '" + x + "'")

    if CAT == "ws":
        while x == " " or x == "\t":
            if i == ln - 1:
                i = -1
                break
            i = i + 1
            x = s[i]
        return [CAT, i, 0]
    elif CAT == "id":
        VAL = ""
        if x == "*":
            VAL = x
            i = i + 1
        while x.isalnum() or x == "_":
            VAL = VAL + x
            if i == ln - 1:
                i = -1
                break
            i = i + 1
            x = s[i]
        if len(VAL) == 1:
            return [CAT, i, VAL]
        if (VAL[0] == "r" or VAL[0] == "R") and VAL[1].isdigit():
            CAT = "reg"
            reg = int(VAL[1])
            if reg > 3:
                raise LE(i, "Illegal register number " + str(reg))
            return [CAT, i, reg]
        return [CAT, i, VAL]
    elif CAT == "par":
        if i < ln - 1:
            if not s[i + 1].isdigit():
                raise LE(i, "Expect a digit after a $")
            return [CAT, i + 2, int(s[i + 1])]
    elif CAT == "num":
        if ln - 1 >= i + 1 and s[i : i + 2] == "0x":
            if ctx.got_minus:
                raise LE(i, "Signed hexadecimal not allowed")
            if ln - 1 < i + 3:
                raise LE(i, "Illegal hexadecimal")
            k = hexbyte(s[i + 2 : i + 4])
            if k < 0:
                raise LE(i, "Illegal hexadecimal")
            if ln - 1 > i + 3:
                return [CAT, i + 4, k]
            else:
                return [CAT, -1, k]

        if ln - 1 >= i + 1 and s[i : i + 2] == "0b":
            if ctx.got_minus:
                raise LE(i, "Signed binary not allowed")
            if ln - 1 < i + 9:
                raise LE(i, "Illegal binary")
            k = 0
            for x in s[i + 2 : i + 10]:
                if "01".find(x) < 0:
                    raise LE(i, "Illegal binary")
                k = k * 2 + int(x)
            if ln - 1 > i + 9:
                return [CAT, i + 10, k]
            else:
                return [CAT, -1, k]

        k = 0
        ctx.got_minus = False
        while x.isdigit():
            k = 10 * k + int(x)
            if i == ln - 1:
                if k > 255:
                    raise LE(i, "Decimal out of range")
                return [CAT, -1, k]
            else:
                i = i + 1
                x = s[i]
        if k > 255:
            raise LE(i, "Decimal out of range")
        return [CAT, i, k]
    elif CAT == "str":
        w = ""
        x = ""
        while x != '"':
            if i == ln - 1:
                raise LE(i, "Runaway string")
            if x != "\\":
                w = w + x
                i = i + 1
            elif s[i + 1] == "\\":
                w = w + x
                i = i + 2
            elif s[i + 1] == '"':
                w = w + '"'
                i = i + 2
            else:
                raise LE(i, "Unknown escape character \\" + s[i + 1])
            x = s[i]
        if i == ln - 1:
            return [CAT, -1, w]
        else:
            return [CAT, i + 1, w]

    else:
        if ln == 1:
            i = -1
        else:
            i = i + 1
        if CAT == "-":
            ctx.got_minus = True
        else:
            ctx.got_minus = False
        return [CAT, i, 0]


def lexline(ctx, linum, s):
    global err_line
    ctx.got_minus = False
    s0 = s
    r = []  # type: List[Tuple[str, Union[str,int], int]]
    ind = 0
    ptr = 0
    while ind >= 0:
        cat = ""
        val = 0
        ind = 0
        try:
            [cat, ind, val] = lex(ctx, s)
            # print("**", cat)# debug
        except LE as e:
            err_line = linum  # Picked up by cocoide
            EP(
                "On line "
                + str(linum)
                + " \n"
                + str(s0[0 : ptr + e.ind])
                + str(s0[ptr + e.ind :])
                + "\nERROR: "
                + e.msg
            )
        # if not cat or not ind or not val:
        #    err_line = linum # Picked up by cocoide
        #    EP( "On line "+str(linum)+ "ERROR: Bad OP Code" )
        if (cat == "emp" and len(r) == 0) or cat != "emp":
            r = r + [(cat, val, ptr)]
        if ind >= 0:
            ptr += ind
        s = s[ind:]
    return r


def asmline(ctx, s, linum, passno):
    global error_msg, err_line

    def parse_exp(lst, onlyabs=False):
        gotrel = False
        relcontext = ctx.sect_name != "$abs"
        opsynt = [lst[j][0] for j in range(3)]
        if opsynt[0:2] == ["num", "end"]:
            return (lst[0][1], gotrel)
        if opsynt[0] == "id":
            lbl = lst[0][1]
            if ctx.sect_name and lbl in ctx.labels[ctx.sect_name]:
                Value = ctx.labels[ctx.sect_name][lbl]
                if relcontext and lbl not in ctx.exts:
                    gotrel = True
            elif lbl in ctx.abses:
                Value = ctx.abses[lbl]
                gotrel = False
            elif lbl == "*":
                Value = ctx.counter
                gotrel = relcontext
            else:
                if opsynt[1] == ":":
                    raise SE(ctx, -1, lst[2][1])
                raise SE(ctx, lst[0][2], "Label " + lbl + " not found")
            if opsynt[1] == "end" or opsynt[1] == ":":
                if onlyabs and gotrel:
                    raise SE(ctx, lst[0][2], "Only absolute labels allowed here")
                return (Value, gotrel)
            if opsynt[1] == "+":
                sign = 1
            elif opsynt[1] == "-":
                sign = -1
            else:
                raise SE(ctx, lst[1][2], "Only + or - allowed here")
            # extension for NSU ######################

            if opsynt[2] == "id":
                lbl2 = lst[2][1]
                if lbl2 in ctx.exts:
                    raise SE(
                        ctx,
                        lst[2][2],
                        "External label " + lbl2 + " can't be used as displacement",
                    )
                if ctx.sect_name and lbl2 in ctx.labels[ctx.sect_name] or lbl2 == "*":
                    Value2 = (
                        ctx.counter if lbl2 == "*" else ctx.labels[ctx.sect_name][lbl2]
                    )
                    if relcontext and lbl2 not in ctx.exts and gotrel:
                        if sign == 1:
                            raise SE(
                                ctx, lst[2][2], "Relocatables can only be subtracted"
                            )
                        else:
                            gotrel = False  # difference between two relocs
                    if gotrel and onlyabs:
                        raise SE(
                            ctx, lst[0][2], "Only absolute result is acceptable here"
                        )
                    return (((Value + sign * Value2) + 256) % 256, gotrel)
                if lbl2 in ctx.abses:
                    if gotrel and onlyabs:
                        raise SE(
                            ctx, lst[0][2], "Only absolute result is acceptable here"
                        )
                    Value2 = ctx.abses[lbl2]
                    return (((Value + sign * Value2) + 256) % 256, gotrel)
                raise SE(ctx, lst[2][2], "Label " + lbl2 + " not found")

            ########################################
            elif opsynt[2] == "num":
                if onlyabs and gotrel:
                    raise SE(ctx, lst[0][2], "Only absolute labels allowed here")
                return (((Value + sign * lst[2][1]) + 256) % 256, gotrel)
            else:
                raise SE(ctx, lst[2][2], "Expecting a number or a label here")
        elif opsynt[0:3] == ["-", "num", "end"]:
            if lst[1][1] > 128:
                raise SE(ctx, lst[1][2], "Negative out of range")
            return (((lst[1][1] ^ 0xFF) + 1) % 256, gotrel)
        else:
            raise SE(ctx, lst[0][2], "Label or number expected")

    def test_end(item):
        if item[0] != "end":
            raise SE(ctx, item[2], "Unexpected text")
        return 0

    cmd = lexline(ctx, linum, s) + [("end", 0, 0)] * 3
    if error_msg != "":
        return None
    if cmd[0][0] == "emp":
        return ("", 0, [])
    if cmd[0][0] != "id":
        raise SE(ctx, cmd[0][2], "Label or opcode expected")
    else:
        next = 1
        label = ""
        opcode = str(cmd[0][1])
        pos = cmd[0][2]
        if cmd[1][0] == ":" or cmd[1][0] == ">":
            if cmd[2][0] == "id" or cmd[2][0] == "end":
                next = 3
                if cmd[1][0] == ":":
                    label = str(cmd[0][1])
                else:
                    label = ">" + str(cmd[0][1])
                opcode = str(cmd[2][1])
                pos = cmd[2][2]
                if cmd[2][0] == "end":
                    return (label, 0, [])
            else:
                raise SE(ctx, cmd[2][2], "Illegal opcode")
        if opcode not in iset:
            # print(pos, "Invalid opcode: "+opcode)#debug
            raise SE(ctx, pos, "Invalid opcode: " + opcode)
        (bincode, cat) = iset[opcode]
        if cat == bi:
            if cmd[next][0] != "reg":
                raise SE(ctx, cmd[next][2], "Register expected")
            if cmd[next + 1][0] != ",":
                raise SE(ctx, cmd[next][2], "Comma expected")
            if cmd[next + 2][0] != "reg":
                raise SE(ctx, cmd[next + 2][2], "Register expected")
            test_end(cmd[next + 3])
            x = bincode + 4 * int(cmd[next][1]) + int(cmd[next + 2][1])
            return (label, 1, [x])
        if cat == un:
            # print("*", args.v3)#debug
            # if opcode in ("ldsp","stsp") and not args.v3: raise SE(ctx, cmd[next][2],"Use option -v3 to compile Mark 3 instructions")
            if opcode in ("ldsa", "addsp", "setsp", "pushall", "popall") and ctx.v3:
                raise SE(
                    ctx, cmd[next][2], "option -v3 forbids use of Mark 4 instructions"
                )
            if cmd[next][0] != "reg":
                raise SE(ctx, cmd[next][2], "Register expected")

            if cmd[next][0] != "reg":
                raise SE(ctx, cmd[next][2], "Register expected")
            x = bincode + int(cmd[next][1])
            if opcode == "ldi" or opcode == "ldsa":
                if cmd[next + 1][0] != ",":
                    raise SE(ctx, cmd[next + 1][2], "Comma expected")
                if passno == 1:
                    return (label, 2, [x, 0])
                elif cmd[next + 2][0] == "str":
                    strVal = str(cmd[next + 2][1])
                    if len(strVal) > 1:
                        raise SE(ctx, cmd[next + 2][2], "Single character expected")
                    if opcode == "ldsa":
                        raise SE(
                            ctx,
                            cmd[next + 2][2],
                            "ldsa requires a number or a template field",
                        )
                    return (label, 2, [x, ord(strVal[0])])
                elif cmd[next + 3][0] == ".":  # template reference
                    if cmd[next + 2][0] != "id":
                        raise SE(ctx, cmd[next + 2][2], "Template name expected")
                    if cmd[next + 2][1] not in ctx.tpls:
                        raise SE(ctx, cmd[next + 2][2], "Unknown template")
                    tn = cmd[next + 2][1]
                    if cmd[next + 4][0] != "id":
                        raise SE(ctx, cmd[next + 4][2], "Field name expected")
                    if cmd[next + 4][1] not in ctx.tpls[tn]:
                        raise SE(ctx, cmd[next + 4][2], "Unknown field name")
                    if cmd[next + 5][0] != "end":
                        raise SE(
                            ctx,
                            cmd[next + 5][2],
                            "unexpected token after template field",
                        )
                    y = ctx.tpls[tn][cmd[next + 4][1]]
                    return (label, 2, [x, y])
                else:
                    Value, gotrel = parse_exp(cmd[next + 2 : next + 5])
                    test_end(cmd[next + 5])
                    if ctx.rel and gotrel:
                        ctx.rel_list[ctx.sect_name] += [ctx.counter + 1]
                    if (
                        cmd[next + 2][0] == "id"
                        and cmd[next + 2][1] in ctx.exts
                        and not ctx.macdef
                    ):
                        ctx.exts[cmd[next + 2][1]] += [(ctx.sect_name, ctx.counter + 1)]
                    return (label, 2, [x, Value])
            else:
                if cmd[next + 1][0] != "end":
                    raise SE(ctx, cmd[next + 1][2], "Only one operand expected")
                return (label, 1, [x])

        if cat == br:
            if passno == 1:
                if opcode == "lchk":
                    return (label, 0, [])
                return (label, 2, [bincode, 0])
            else:
                if opcode == "ldsa" and cmd[next + 2][0] not in ("num", "-"):
                    raise SE(
                        ctx,
                        cmd[next + 2][2],
                        "ldsa requires a number or a template field",
                    )
                Value, gotrel = parse_exp(cmd[next : next + 3])
                test_end(cmd[next + 3])
                if ctx.rel and opcode != "lchk" and gotrel:
                    ctx.rel_list[ctx.sect_name] += [ctx.counter + 1]
                if cmd[next][0] == "id" and cmd[next][1] in ctx.exts and not ctx.macdef:
                    ctx.exts[cmd[next][1]] += [(ctx.sect_name, ctx.counter + 1)]
                if opcode == "lchk":
                    return (label, 0, [])
                return (label, 2, [bincode, Value])
        if cat == osix:
            if cmd[next][0] != "num":
                raise SE(ctx, cmd[next][2], "Number expected")
            test_end(cmd[next + 1])
            return (label, 2, [bincode, cmd[next][1]])

        if cat == zer:
            return (label, 1, [bincode])

        if cat == spmove:  # addsp/setsp
            if passno == 1:
                return (label, 2, [0, 0])
            mynext = next
            mymult = 1
            if cmd[mynext][0] == "-":
                mynext = next + 1
                mymult = -1
            if cmd[mynext][0] == "num":
                test_end(cmd[mynext + 1])
                return (label, 2, [bincode, mymult * cmd[mynext][1]])

            if (
                cmd[mynext][0] != "id"
                or cmd[mynext + 1][0] != "."
                or cmd[mynext + 2][0] != "id"
            ):
                raise SE(
                    ctx,
                    cmd[mynext][2],
                    "addsp/setsp instructions require a number or a template field operand",
                )
            if cmd[mynext][1] not in ctx.tpls:
                raise SE(
                    ctx,
                    cmd[mynext][2],
                    "Unknown template '" + str(cmd[mynext][1]) + "'",
                )
            test_end(cmd[mynext + 3])
            tn = cmd[mynext][1]
            return (label, 2, [bincode, mymult * ctx.tpls[tn][cmd[mynext + 2][1]]])

        ################################################## M A C R O FACILITIES
        if cat == mc:
            if opcode == "macro":
                if ctx.macdef:
                    return ("", -3, [])
                if label != "":
                    raise SE(ctx, 0, "Label not allowed")
                if cmd[next][0] != "id":
                    raise SE(ctx, cmd[next][2], "Name expected")
                ctx.mname = str(cmd[next][1])
                if ctx.mname in iset:
                    if iset[ctx.mname][1] != mi:
                        raise SE(
                            ctx,
                            cmd[next][2],
                            "Opcode '" + ctx.mname + "' reserved by assembler",
                        )
                if cmd[next + 1][0] != "/":
                    raise SE(ctx, cmd[next + 1][2], "/ expected")
                if cmd[next + 2][0] != "num":
                    raise SE(ctx, cmd[next + 2][2], "Number expected")
                test_end(cmd[next + 3])
                ctx.marity = cmd[next + 2][1]
                return ("", -3, [])
            elif opcode == "mend":
                test_end(cmd[next])
                return ("", -4, [])
        if cat == mi:
            if passno == 2 or ctx.macdef:
                return ("", 0, [])
            ctx.mcalls += 1
            if ctx.mcalls > 800:
                raise SE(ctx, 0, "Too many macro expansions [>800]")
            ctx.pars = commasep(ctx, cmd[next:])
            parno = len(ctx.pars)
            if opcode + "/" + str(parno) not in ctx.macros:
                raise SE(
                    ctx,
                    cmd[next][2],
                    "Number of params ("
                    + str(parno)
                    + ")does not match definition of macro "
                    + opcode,
                )

            if label == "":
                ll = []
            elif label[0] == ">":
                ll = [label[1:] + ">"]
            else:
                ll = [label + ":"]

            mbody = (
                ["# >>>>>>"] + ll + ctx.macros[opcode + "/" + str(parno)] + ["# <<<<<<"]
            )
            newbody = []
            for s1 in mbody:
                if ctx.dbg:
                    print(
                        "before => "
                        + s1
                        + " ******* pars= "
                        + str(ctx.pars)
                        + "mvars="
                        + str(ctx.mvars)
                    )
                rslt = mxpand(ctx, s1, 0, parno)
                if ctx.dbg:
                    print("after  => " + str(rslt))
                if not ismstack(ctx, linum, rslt):
                    newbody += [rslt + "#" + chr(1)]
            ctx.mcount += 1
            return ("", -5, newbody)
        ################################################## END OF MACRO FACILITIES

        if ctx.macdef:
            return ("", 0, [])
        if cat == spec:
            if opcode == "ds":
                Value, _ = parse_exp(cmd[next : next + 3], onlyabs=True)
                ctx.ds_ins = True
                return (label, Value, [0] * Value)
            if opcode == "set":
                if cmd[next][0] != "id":
                    raise SE(ctx, cmd[next + 1][2], "Identifier expected")
                if cmd[next + 1][0] != "=":
                    raise SE(ctx, cmd[next + 1][2], "'=' expected")
                Value, _ = parse_exp(cmd[next + 2 : next + 5], onlyabs=True)
                if passno == 2:
                    return (label, -10, [Value])
                alias = str(cmd[next][1])
                if alias in ctx.abses:
                    raise SE(ctx, cmd[next + 1][2], alias + " already defined")
                ctx.abses[alias] = Value
                return (label, -10, [Value])
            if opcode == "dc":
                img = []
                empty = True
                ctx.ds_ins = True
                while cmd[next][0] != "end":
                    empty = False
                    if cmd[next][0] == "num":
                        img += [cmd[next][1]]
                    elif cmd[next][0] == "-" and cmd[next + 1][0] == "num":
                        if int(cmd[next + 1][1]) > 128:
                            raise SE(ctx, cmd[next + 1][2], "Negative out of range")
                        img += [((int(cmd[next + 1][1]) ^ 255) + 1) % 256]
                        next += 1
                    elif cmd[next][0] == "str":
                        for c in str(cmd[next][1]):
                            img += [ord(c)]
                    elif cmd[next][0] == "id":
                        if passno == 1:
                            img += [0]
                            if cmd[next + 1][0] == "+" or cmd[next + 1][0] == "-":
                                next += 2
                        else:
                            exp = cmd[next : next + 3]
                            Value, gotrel = parse_exp(
                                [x if x[0] != "," else ["end", 0, 0] for x in exp]
                            )
                            if ctx.rel and gotrel:
                                ctx.rel_list[ctx.sect_name] += [ctx.counter + len(img)]
                            if (
                                cmd[next][0] == "id"
                                and cmd[next][1] in ctx.exts
                                and not ctx.macdef
                            ):
                                ctx.exts[cmd[next][1]] += [
                                    (ctx.sect_name, ctx.counter + len(img))
                                ]

                            img += [Value]

                            if cmd[next + 1][0] == "+" or cmd[next + 1][0] == "-":
                                next += 2

                    else:
                        raise SE(ctx, cmd[next][2], "Illegal constant")

                    if cmd[next + 1][0] == ",":
                        empty = True
                        next += 2
                    elif cmd[next + 1][0] != "end":
                        raise SE(ctx, cmd[next + 1][2], "Illegal separator")
                    else:
                        return (label, len(img), img)
                if empty:
                    raise SE(ctx, cmd[next][2], "Data expected")

            if opcode == "asect":
                if label != "":
                    raise SE(ctx, 0, "Label not allowed")
                if cmd[next][0] != "num":
                    raise SE(ctx, cmd[next][2], "Numerical address expected")
                addr = int(cmd[next][1])
                if addr < 0:
                    raise SE(ctx, cmd[next][2], "Illegal number")
                test_end(cmd[next + 1])
                if ctx.rel:
                    ctx.rsects[ctx.sect_name] = ctx.counter
                    ctx.rel = False
                if ctx.tpl:
                    ctx.tpl = False
                    ctx.tpls[ctx.tpl_name]["_"] = ctx.counter
                ctx.counter = addr
                ctx.sect_name = "$abs"
                return ("", -1, [])
            if opcode == "tplate":
                if label != "":
                    raise SE(ctx, 0, "Label not allowed")
                if cmd[next][0] != "id":
                    raise SE(ctx, cmd[next][2], "Name expected")
                if ctx.rel:
                    ctx.rsects[ctx.sect_name] = ctx.counter
                ctx.rel = False
                if cmd[next][1] in ctx.tpls and passno == 1:
                    raise SE(ctx, cmd[next][2], "Template already defined")
                ctx.counter = 0
                ctx.tpl = True
                ctx.tpl_name = cmd[next][1]
                if ctx.tpl_name not in ctx.tpls:
                    ctx.tpls[ctx.tpl_name] = {}
                ctx.sect_name = None
                return ("", -1, [])
            if opcode == "rsect":
                if label != "":
                    raise SE(ctx, 0, "Label not allowed")
                if cmd[next][0] != "id":
                    raise SE(ctx, cmd[next][2], "Name expected")
                test_end(cmd[next + 1])
                if ctx.rel:
                    ctx.rsects[ctx.sect_name] = ctx.counter
                ctx.rel = True
                if ctx.tpl:
                    ctx.tpl = False
                    ctx.tpls[ctx.tpl_name]["_"] = ctx.counter
                ctx.sect_name = cmd[next][1]
                if ctx.sect_name not in ctx.rsects:
                    ctx.rsects[ctx.sect_name] = 0
                    ctx.counter = 0
                    ctx.labels[ctx.sect_name] = {}
                    ctx.ents[ctx.sect_name] = {}
                    ctx.rel_list[ctx.sect_name] = []
                else:
                    ctx.counter = ctx.rsects[ctx.sect_name]
                return (label, -1, cmd[next][1])
            if opcode == "ext":
                test_end(cmd[next])
                if label not in ctx.exts or label not in ctx.labels[ctx.sect_name]:
                    ctx.exts[label] = []
                    return ("!" + label, 0, cmd[next][1])
                return ("", 0, [])
            if opcode == "end":
                if label != "":
                    raise SE(ctx, 0, "Illegal label")
                if ctx.rel == True:
                    ctx.rsects[ctx.sect_name] = ctx.counter
                if passno == 1:
                    if ctx.tpl:
                        ctx.tpls[ctx.tpl_name]["_"] = ctx.counter
                        ctx.tpl = False
                    for name in ctx.rsects:
                        ctx.rsects[name] = 0
                ctx.rel = False
                return ("$$$", -2, [])
        else:
            err_line = linum
            EP("Internal error: " + opcode + " " + str(cat) + str(linum))

    return None


def asm(ctx, assmtext=None):
    global err_line

    if assmtext != None:
        ctx.text = assmtext

    output = []  # type: List[Tuple[int, int, List[str], str]]
    ctx.generated = len(ctx.text) * [False]
    for passno in [1, 2]:
        linum = 0
        linind = 0
        ready = False
        finished = False
        size = 0
        label = ""
        code = []
        while True:
            if linind <= len(ctx.text) - 1:
                s = ctx.text[linind]
                if not ctx.generated[linind]:
                    linum += 1
                linind += 1
            else:
                break

            try:
                # try:
                (label, size, code) = asmline(ctx, s, linum, passno)
                # if passno==1: print linum, ":", (label,size,code), s
            # except TypeError:
            # if error_msg != "":return
            except SE as e:
                if not ctx.macdef:
                    if e.ind >= 1:
                        EP(s[0 : e.ind] + s[e.ind :], term=False)
                        # EP (" "*(e.ind))
                    elif e.ind != -1:
                        EP(s, term=False)
                    err_line = linum
                    EP("On line " + str(linum) + " ERROR: " + e.msg)
                    return
                else:
                    size = 0
            except TypeError:
                err_line = linum
                return

            if ctx.macdef and size != -4 and size != -3:  # accumulate macro definition
                if passno == 1:
                    mbody += [s]
                continue
            if size == -1:  # sects
                ready = True
                continue
            elif size == -2:  # end
                if ctx.macdef:
                    EP("ERROR: 'end' encountered while processing macro definition")
                    quit(-1)
                finished = True
                break
            elif size == -3:  # macro
                if ctx.macdef:
                    EP("ERROR: macro definition inside macro")
                    quit(-1)
                ctx.macdef = True
                mbody = []  # type: List[str]
                continue
            elif size == -4:  # mend
                if not ctx.macdef:
                    EP("ERROR: mend before macro")
                    quit(-1)
                ctx.macdef = False
                if passno == 1:
                    ctx.macros[ctx.mname + "/" + str(ctx.marity)] = mbody
                    iset[ctx.mname] = (0, mi)
                continue

            elif size == -5:  # macro expansion
                ctx.text = ctx.text[0:linind] + code + ctx.text[linind:]
                ctx.generated = (
                    ctx.generated[0:linind]
                    + len(code) * [True]
                    + ctx.generated[linind:]
                )
                continue

            elif size == -10:  # set
                if passno == 2:
                    output += [
                        (linind, code[0], [], "")
                    ]  # dummy output to get addresses in listing
                continue
            elif size >= 0:  # deal with the label off a true instruction
                if ctx.tpl and passno == 1:
                    if not ctx.ds_ins and size > 0:
                        err_line = linum
                        EP(
                            "On line "
                            + str(linum)
                            + " ERROR: Only dc/ds allowed in templates"
                        )
                    ctx.ds_ins = False
                if label != "" and passno == 1:
                    if not ready:
                        err_line = linum
                        EP(
                            "On line "
                            + str(linum)
                            + " ERROR: 'asect' or 'rsect' expected"
                        )
                    addr = ctx.counter
                    if ctx.tpl:
                        if label[0] == ">":
                            err_line = linum
                            EP(
                                "On line "
                                + str(linum)
                                + " ERROR: exts in template not allowed"
                            )
                        if label in ctx.tpls[ctx.tpl_name]:
                            err_line = linum
                            EP(
                                "On line "
                                + str(linum)
                                + " ERROR: Label '"
                                + label
                                + "' already defined"
                            )
                        ctx.tpls[ctx.tpl_name][label] = ctx.counter
                    if label[0] == ">":
                        label = label[1:]
                        ctx.ents[ctx.sect_name][label] = ctx.counter
                    if label[0] == "!":
                        if label[1] == ">":
                            err_line = linum
                            EP(
                                "On line "
                                + str(linum)
                                + " ERROR: label "
                                + label[2:]
                                + " both ext and entry"
                            )
                        label = label[1:]
                        addr = 0
                    if not ctx.tpl and label in ctx.labels[ctx.sect_name]:
                        err_line = linum
                        EP(
                            "On line "
                            + str(linum)
                            + " ERROR: label "
                            + label
                            + " already defined"
                        )
                    if not ctx.tpl:
                        ctx.labels[ctx.sect_name][label] = addr
                    if not ctx.rel:
                        ctx.abses[label] = ctx.counter

            if passno == 2 and size > 0 and not ctx.tpl:
                if not ready:
                    err_line = linum
                    EP("On line " + str(linum) + " ERROR: 'asect' or 'rsect' expected")
                output += [(linind, ctx.counter, code, ctx.sect_name)]
            if passno == 2 and ctx.tpl:
                output += [
                    (linind, ctx.counter, [], "")
                ]  # dummy output to get addresses in listing
            if size > 0:
                ctx.counter += size
        if not finished:
            EP("ERROR: file ends before end of program")
    return output


def shex(k):
    m = k
    if m < 0:
        m = 256 + m
    return format(m, "02x")[:2]


def pretty_print(ctx, obj1, src, prtOP=True):
    def ismex(s):
        return s[-2:] == "#" + chr(1)

    obj = obj1

    # if not prtOP:
    #    offset=20
    # else:
    offset = 15

    if prtOP == True:
        print(
            "\nCdM-8 Assembler v"
            + ASM_VER
            + " <<<"
            + ctx.filename
            + ".asm>>> "
            + time.strftime("%d/%m/%Y")
            + " "
            + time.strftime("%H:%M:%S")
            + "\n"
        )
    else:
        # return code listing via function return (to cocoide)
        retlist = ""
        ctx.lst_me = False

    me_skip = False

    if ctx.lst_me:  # remove macro expansion markers from the source lines
        src1 = []
        for s in src:
            slong = s
            while ismex(slong):
                slong = slong[:-2]
            src1 += [slong]
        src = src1

    ln = 0
    for lnind in range(len(src)):
        if not ctx.generated[lnind] or ctx.lst_me:
            ln += 1

        s = src[lnind]

        if me_skip and ismex(s):
            continue
        else:
            me_skip = False

        if (
            lnind + 1 <= len(src) - 1 and not ismex(s) and ismex(src[lnind + 1])
        ):  # we are inside macro expansion and must not list it
            last_line_ind = lnind + 1
            while last_line_ind <= len(src) - 1:
                if not ismex(src[last_line_ind]):
                    break
                else:
                    last_line_ind += 1
            last_line_ind -= 1
            last_line = last_line_ind + 1
            me_skip = True

            if obj == [] or (
                obj != [] and obj[0][0] > last_line
            ):  # macro produced no code
                if prtOP == True:
                    print(
                        " " * offset + " " + format(ln, "3d") + "  " + s
                    )  # just print the mi
                else:
                    retlist += " " * offset + " " + format(ln, "3d") + s + "\n"

                continue
            else:
                addr = obj[0][1]
                clist = obj[0][2]
                secname = obj[0][3]
                a1 = addr + len(clist)
                k = 1
                frag = False
                while k <= len(obj) - 1 and obj[k][0] <= last_line:
                    if obj[k][1] == a1 and obj[k][3] == secname:
                        clist += obj[k][2]
                        a1 += len(obj[k][2])
                    else:
                        if prtOP == True:
                            print(
                                ("<scattered>" + " " * offset)[0:offset]
                                + " "
                                + format(ln, "3d")
                                + "  "
                                + s
                            )
                        else:
                            retlist += (
                                ("<scattered>" + " " * offset)[0:offset]
                                + " "
                                + format(ln, "3d")
                                + "\n"
                            )
                        frag = True
                        break
                    k += 1

                if frag:
                    while k <= len(obj) - 1 and obj[k][0] <= last_line:
                        k += 1
                    obj = obj[k:]
                    continue
                else:
                    obj = [(lnind + 1, addr, clist, secname)] + obj[k:]

        if obj == [] or obj[0][0] != lnind + 1:
            if prtOP == True:
                print(" " * offset + " " + format(ln, "3d") + "  " + s)
            else:
                retlist += " " * offset + " " + format(ln, "3d") + "  " + s + "\n"
        else:
            addr = obj[0][1]
            clist = obj[0][2]
            secname = obj[0][3]
            obj = obj[1:]
            tstr = s
            ln1 = ln
            if secname == "":  # template
                if prtOP == True:
                    print(
                        (format(addr, "02x") + ": " + " " * offset)[0:offset]
                        + " "
                        + format(ln1, "3d")
                        + "  "
                        + s
                    )
                else:
                    retlist += (
                        (format(addr, "02x") + ": " + " " * offset)[0:offset]
                        + " "
                        + format(ln1, "3d")
                        + "  "
                        + s
                        + "\n"
                    )
            while clist != []:
                pstr = format(addr, "02x") + ": " + (" ".join(map(shex, clist[0:4])))
                ppr = (pstr + " " * offset)[0:offset]
                if ln1 > 0:
                    sln = format(ln1, "3d")
                else:
                    sln = " "
                if prtOP == True:
                    print(ppr + " " + sln + "  " + tstr)
                else:
                    retlist += ppr + " " + sln + "  " + tstr + "\n"
                if len(clist) <= 4:
                    break
                addr += 4
                tstr = " "
                ln1 = 0
                clist = clist[4:]

    if prtOP == True:  # Not needed for cocide
        print("\n" + "=" * 70)
        print("\nSECTIONS:\nName\tSize\tRelocation offsets\n")

        for name in ctx.rsects:
            relsn = ctx.rel_list[name]
            strg = ""
            for r in relsn:
                strg += format(r, "02x") + " "
            print(name + "\t" + format(ctx.rsects[name], "02x") + "\t" + strg)

        print("\nENTRIES:\nSection\t\tName/Offset\n")
        for name in ctx.ents:
            strg = name + "\t\t"
            if ctx.ents[name] == {}:
                strg += "<NONE>"
                print(strg)
                continue
            for nm in ctx.ents[name]:
                strg += nm + ":" + format(ctx.ents[name][nm], "02x") + "\t"
            print(strg)

        print("\nEXTERNALS:\nName\t\tUsed in\n")
        for name in ctx.exts:
            strg = name + "\t\t"
            for pair in ctx.exts[name]:
                (nm, oset) = pair
                strg += nm + "+" + format(oset, "02x") + " "
            print(strg)
        print("\n" + 70 * "=")
    else:
        return retlist


def genoc(ctx, output, objbuff=None):
    def eladj(absegs):
        if len(absegs) < 2:  # elimenate adjacent segments
            return absegs
        x, y, w = absegs[0], absegs[1], absegs[2:]
        if x[0] + len(x[1]) == y[0]:  # adjacent: merge into one
            return eladj([(x[0], x[1] + y[1])] + w)
        else:
            return [x] + eladj([y] + w)

    if objbuff == None:
        objfile = open(ctx.filename + ".obj", "w")
    else:
        objbuff = ""
    sects = {}  # type: Dict[str, List[str]]
    absegs = []
    for r in output:
        s = r[3]
        a = r[1]
        d = r[2]
        if s == "":
            continue
        if s != "$abs":
            if s not in sects:
                sects[s] = []
            sects[s] += d
        else:
            absegs += [(a, d)]
    absegs = eladj(absegs)
    for pair in absegs:
        (a, d) = pair
        if objbuff == None:
            objfile.write(
                "ABS  " + format(a, "02x") + ": " + " ".join(map(shex, d)) + "\n"
            )
        else:
            objbuff += "ABS  " + format(a, "02x") + ": " + " ".join(map(shex, d)) + "\n"

    en = ctx.ents["$abs"]
    for e in en:
        if objbuff == None:
            objfile.write("NTRY " + e + " " + shex(en[e]) + "\n")
        else:
            objbuff += "NTRY " + e + " " + shex(en[e]) + "\n"

    for st in sects:
        if objbuff == None:
            objfile.write("NAME " + st + "\n")
            objfile.write("DATA " + " ".join(map(shex, sects[st])) + "\n")
            objfile.write("REL  " + " ".join(map(shex, ctx.rel_list[st])) + "\n")
            en = ctx.ents[st]
            for e in en:
                objfile.write("NTRY " + e + " " + shex(en[e]) + "\n")
        else:
            objbuff += "NAME " + st + "\n" + "DATA "
            objbuff += " ".join(map(shex, sects[st])) + "\n"
            objbuff += "REL  " + " ".join(map(shex, ctx.rel_list[st])) + "\n"
            en = ctx.ents[st]
            for e in en:
                objbuff += "NTRY " + e + " " + shex(en[e]) + "\n"

    for extn in ctx.exts:
        strg = "XTRN " + extn + ":"
        if ctx.exts[extn] == []:
            EP("WARNING: ext '" + extn + "' declared, not used")
        for pair in ctx.exts[extn]:
            (s, offset) = pair
            strg += " " + s + " " + shex(offset)
        if objbuff == None:
            objfile.write(strg + "\n")
        else:
            objbuff += strg + "\n"

    if objbuff == None:
        objfile.close()
    else:
        return objbuff
    return


def takemdefs(ctx, objfile, filename):
    def formerr():
        EP(
            "Error in macro library file '"
            + filename
            + "' On line "
            + str(ln)
            + ":\n"
            + l
        )

    name = ""
    body = []
    opcode = ""

    state = 0
    ln = 0
    for l in objfile:
        l = l.rstrip()
        ln += 1
        if l == "" or l[0] == "#":
            continue
        if state == 1:
            if l[0] != "*":
                body += [l]
            else:
                ctx.macros[name] = body
                iset[opcode] = (0, mi)
                state = 0
        if state == 0:
            if not l[0] == "*":
                formerr()
            if not l[1].isalpha():
                formerr()
            k = 2
            found = False
            while k <= len(l) - 1:
                if not (l[k].isalnum() or l[k] == "_"):
                    found = True
                    break
                k += 1
            if not found:
                formerr()
            if l[k] != "/":
                formerr()
            opcode = l[1:k]
            k += 1
            if k > len(l) or not l[k].isdigit():
                formerr()
            name = l[1 : k + 1]
            body = []
            state = 1
    ctx.macros[name] = body
    iset[opcode] = (0, mi)


###################### M A C R O  FACILITIES
#


def EP(s, term=True):
    global ret_error, error_msg
    # print("**", retError)
    if ret_error:
        error_msg = s
        # if error_msg !="":
        #    error_msg = error_msg + "\n"+s
    else:
        sys.stderr.write(s + "\n")
        if term:
            quit(-1)
    # print(error_msg)#debug


def mxpand(ctx, s, pos, pno):
    # substitute factual pars for $1...$<pno> in s escaping quoted strings
    # substitute a nonce for ' and strings for ?<id> from mvars

    if s == "":
        return ""
    if len(s) == 1 and s == "$":
        raise SE(ctx, pos, "Missing parameter number")
    x = s[0]

    if x == "$":
        if not s[1].isdigit:
            raise SE(ctx, pos, "Illegal parameter number")
        n = int(s[1])
        if n > pno:
            raise SE(ctx, pos, "Parameter number too high")
        k = len(ctx.pars[n - 1])
        return ctx.pars[n - 1] + mxpand(ctx, s[2:], pos + k - 2, pno)

    if x == "?":
        return mxpand(ctx, "!" + mxpand(ctx, s[1:], pos + 1, pno), pos, pno)
    if x == "!":
        k = 1
        w = ""
        while k <= len(s) - 1:
            if s[k].isalnum():
                w += s[k]
                k += 1
            else:
                break
        if w == "":
            if len(s) == 1:
                ofc = ""
            else:
                ofc = s[1]
            raise SE(ctx, pos, "Illegal macro-variable '" + ofc + "'")
        if w not in ctx.mvars:
            raise SE(ctx, pos, "Unassigned macro-variable: " + w)
        return ctx.mvars[w] + mxpand(ctx, s[k:], pos + len(ctx.mvars[w]), pno)

    if x == "'":
        smcount = str(ctx.mcount)
        return smcount + mxpand(ctx, s[1:], pos + len(smcount), pno)
    if x == '"':
        k = 1
        esc = False
        while k <= len(s) - 1:
            if esc:
                esc = False
                continue
            if s[k] == "\\":
                esc = True
                continue
            v = s[k]
            if v == '"':
                return s[: k + 1] + mxpand(ctx, s[k + 1 :], pos + k + 1, pno)
            k += 1
        return s
    else:
        return x + mxpand(ctx, s[1:], pos + 1, pno)


def unptoken(ctx, t):
    if t[0] == "id":
        return t[1]
    if t[0] == "reg":
        return "r" + str(t[1])
    if t[0] == "num":
        return "0x" + format(t[1] + 256, "02x")[-2:]
    if t[0] == "str":
        return '"' + (t[1].replace("\\", "\\\\")).replace('"', '\\"') + '"'
    raise SE(ctx, t[2], "Illegal item")


def commasep(ctx, tokens):
    k = 0
    result = []  # type: List[str]
    while k <= len(tokens) - 1:
        if tokens[k][0] == "end":
            return result
        else:
            if (
                tokens[k][0] == "id"
                and k <= len(tokens) - 3
                and tokens[k + 1][0] == "."
                and tokens[k + 2][0] == "id"
            ):  # template field
                result += [
                    unptoken(ctx, tokens[k]) + "." + unptoken(ctx, tokens[k + 2])
                ]
                k = k + 2
            else:
                result += [unptoken(ctx, tokens[k])]
        k = k + 1
        if k <= len(tokens) - 1 and tokens[k][0] != "," and tokens[k][0] != "end":
            raise SE(ctx, tokens[k][2], "Comma expected here")
        else:
            k = k + 1
    return result


def ismstack(ctx, l, s):
    global err_line, error_msg

    def diag(pos, msg, brief=False):
        global err_line

        if brief:
            err_line = l
            prefix = "On line " + str(l) + " ERROR: "
        else:
            err_line = l
            prefix = (
                "On line "
                + str(l)
                + " ERROR: Macro \nExpanding:\n"
                + s
                + "\n"
                + (" " * pos)
                + "^\n"
            )
        EP(prefix + msg)

    tokens = lexline(ctx, l, s)
    if error_msg != "":
        return False

    mstackind = 0

    try:
        if len(tokens) >= 1:
            if tokens[0][0] == "num":
                mstackind = int(tokens[0][1])
                if mstackind > len(ctx.mstack) - 1:
                    if len(tokens) > 1:
                        mstpos = tokens[1][2]
                    else:
                        mstpos = 0
                    diag(mstpos, "Macro stack index too high: " + str(mstackind))
                tokens = tokens[1:]

        if len(tokens) == 0:
            return False

        if len(tokens) == 1:
            if tokens[0][0] == "id" and (tokens[0][1] in ["mpush", "mread", "mpop"]):
                diag(0, "Macro stack operation without argument")
            else:
                return False

        if len(tokens) >= 3 and tokens[0][0] == "id" and tokens[1][0] == ":":
            if tokens[2][0] == "id" and (tokens[2][1] in ["mpush", "mread", "mpop"]):
                diag(0, "Macro directives must not be labelled")

        if tokens[0][0] == "id" and tokens[0][1] == "mpush":
            frames = commasep(ctx, tokens[1:])
            ctx.mstack[mstackind] = frames[::-1] + ctx.mstack[mstackind]
            return True

        if tokens[0][0] == "id" and (tokens[0][1] == "mpop" or tokens[0][1] == "mread"):
            diagmes = "Macro stack " + str(mstackind) + " empty or too few frames"
            k = 1
            stoff = 0
            brief = False
            while k < len(tokens):
                if tokens[k][0] == "id":
                    if len(ctx.mstack[mstackind]) < stoff + 1:
                        diag(tokens[k][2], diagmes, brief)
                    if tokens[0][1] == "mpop":
                        ctx.mvars[str(tokens[k][1])] = ctx.mstack[mstackind][0]
                        ctx.mstack[mstackind] = ctx.mstack[mstackind][1:]
                    else:
                        # Macro error here sometimes - fixed??
                        # print("**", k, len(tokens), mstackind, len(mstack), stoff, len(mstack[mstackind]))#debug
                        ctx.mvars[str(tokens[k][1])] = ctx.mstack[mstackind][stoff]
                        stoff += 1
                elif tokens[k][0] == "str":
                    brief = True
                    diagmes = str(tokens[k][1])
                else:
                    diag(
                        tokens[k][2],
                        "Macro variable or diagnostic message expected here",
                    )
                k += 1
                if k <= len(tokens) - 1 and tokens[k][0] != ",":
                    diag(tokens[k][2], "Comma expected here")
                else:
                    k += 1
            return True

        if (
            tokens[0][0] == "id" and tokens[0][1] == "unique"
        ):  # not a macro stack operation but we keep it here for simplicity
            k = 1
            regfree = 4 * [True]
            regmvars = []  # type: List[str]
            howmany = 0
            while k <= len(tokens) - 1:
                howmany += 1
                if tokens[k][0] == "id":
                    regmvars += [str(tokens[k][1])]
                elif tokens[k][0] == "reg":
                    if regfree[int(tokens[k][1])]:
                        regfree[int(tokens[k][1])] = False
                    else:
                        diag(
                            tokens[k][2],
                            "r" + str(tokens[k][1]) + " occurs more than once",
                        )
                else:
                    diag(tokens[k][2], "Macro variable or register expected here")
                k = k + 1
                if k <= len(tokens) - 1 and tokens[k][0] != ",":
                    diag(tokens[k][2], "Comma expected here")
                else:
                    k = k + 1
            if howmany > 4:
                diag(tokens[0][2], "More than 4 operands specified")
            for v in regmvars:
                ctx.mvars[v] = ""
            for v in regmvars:
                for k in [0, 1, 2, 3]:
                    if regfree[k]:
                        regfree[k] = False
                        if ctx.mvars[v] != "":
                            diag(
                                tokens[0][2],
                                "macro var " + v + " occurs more than once",
                            )
                        else:
                            ctx.mvars[v] = "r" + str(k)
                        break
            return True

    except:
        diag(int(tokens[k][1]), "Macro error!", brief=True)

    return False


################################ E N D OF MACRO FACILITIES


def compile_asm(codetext=None, cdm8ver=4, ctx=None):
    """Entry point when imported as a library"""

    global ret_error, err_line, error_msg

    # Init all the global vars

    ret_error = True
    err_line = None
    error_msg = ""

    ctx = ctx or Context(cdm8ver)

    for line in codetext:
        line = line.rstrip()
        ctx.text += [line.expandtabs()]

    mlb_name = "standard.mlb"
    mlb_path = os.path.join(sys.path[0], mlb_name)

    skipfile = False
    try:
        mlibfile = open(mlb_path, "r")
    except IOError:
        skipfile = True

    if skipfile:
        skipfile = False
        try:
            mlibfile = open(mlb_name, "r")
        except IOError:
            skipfile = True
            EP("WARNING: no " + mlb_name + " found")
    if not skipfile:
        takemdefs(ctx, mlibfile, mlb_name)  # "standard.mlb")
        mlibfile.close()
    # print("compiling")

    # print(ctx.text)
    if error_msg != "":
        # print("result", error_msg) #debug
        return None, None, error_msg

    result = asm(ctx)
    if error_msg != "":
        # print("result", error_msg) #debug
        return None, None, error_msg
    objstr = ""
    objstr = genoc(ctx, result, objstr)
    if error_msg != "":
        # print("objstr", error_msg)#debug
        return None, None, error_msg
    codelist = pretty_print(ctx, result, ctx.text, False)
    return objstr, codelist, None


def main():
    parser = argparse.ArgumentParser(description="CdM-8 Assembler v1.0")
    parser.add_argument("filename", nargs="?", type=str, help="source_file[.asm]")
    parser.add_argument(
        "-l",
        dest="lst",
        action="store_const",
        const=True,
        help="Produce program listing",
    )
    parser.add_argument(
        "-lx",
        dest="lstx",
        action="store_const",
        const=True,
        default=False,
        help="Produce program listing showing macro expansion",
    )
    parser.add_argument(
        "-m", dest="mlibs", type=str, nargs="*", help="Macro_library[.mlb]"
    )
    parser.add_argument(
        "-d",
        dest="dbg",
        action="store_const",
        const=True,
        default=False,
        help="Include debug output",
    )
    args = parser.parse_args()
    filename = args.filename
    if not filename:
        # Fire up GUI!
        args.lst = True
        # args.sym=True
        root = tk.Tk()
        root.withdraw()
        cocasGUI = CocAs(master=root, exitroot=True)
        root.mainloop()
    else:
        ctx = Context()
        ctx.filename = filename
        if filename[-4:] == ".asm":
            filename = filename[:-4]
            ctx.filename = filename
        try:
            asmfile = open(filename + ".asm", "r")
        except IOError:
            EP(filename + ".asm: file not found")
        for line in asmfile:
            line = line.rstrip()
            ctx.text += [line.expandtabs()]

        # Test SE (Exceoption)
        # raise SE(ctx, 2,"MIcks MEssage")

        mlb_name = "standard.mlb"
        mlb_path = os.path.join(sys.path[0], mlb_name)

        skipfile = False
        try:
            mlibfile = open(mlb_path, "r")
        except IOError:
            skipfile = True

        if skipfile:
            skipfile = False
            try:
                mlibfile = open(mlb_name, "r")
            except IOError:
                skipfile = True
                EP("WARNING: no " + mlb_name + " found")

        if not skipfile:
            takemdefs(ctx, mlibfile, "standard.mlb")
            mlibfile.close()

        if args.mlibs != None:
            for x in args.mlibs:
                if x[-4:] == ".mlb":
                    x = x[:-4]
                try:
                    mlibfile = open(x + ".mlb", "r")
                except IOError:
                    EP(x + ".mlb not found")
                takemdefs(ctx, mlibfile, x)
                mlibfile.close()

        result = asm(ctx)
        genoc(ctx, result)

        if args.lstx:
            ctx.lst_me = True
        if args.lst or args.lstx:
            pretty_print(ctx, result, ctx.text)
        quit()


if __name__ == "__main__":
    main()
