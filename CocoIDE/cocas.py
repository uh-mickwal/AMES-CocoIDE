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


import argparse
import io
import os
import sys
import time
import tkinter as tk
from enum import Enum, auto
from tkinter import filedialog
from tkinter import scrolledtext as sctx
from tkinter import ttk
from typing import IO, Any, Dict, List, Optional, Tuple, Union

ASM_VER = "2.7"

###################### C D M 8  A S S E M B L E R  Facilities


class Context:
    def __init__(self, cdm8ver: int = 4) -> None:
        if cdm8ver == 4:
            self.v3 = False
        else:
            self.v3 = True
        self.dbg = False
        self.save = False

        self.lst = False

        self.filename: Optional[str] = None
        self.text: List[str] = []
        self.raw_text: List[str] = []
        self.counter = 0
        self.rel = False
        self.rel_list: Dict[str, List[int]] = {}
        self.exts: Dict[str, List[Tuple[Optional[str], int]]] = {}
        self.ents: Dict[str, Dict[str, int]] = {}
        self.abses: Dict[str, int] = {}
        self.labels: Dict[str, Dict[str, int]] = {}
        self.rsects: Dict[str, int] = {}
        self.sect_name: Optional[str] = None
        self.labels["$abs"] = {}
        self.ents["$abs"] = {}
        self.tpls: Dict[str, Dict[str, int]] = {}
        self.tpl = False
        self.ds_ins = False
        self.tpl_name = ""
        self.generated: List[bool] = []
        self.got_minus = False
        self.lst_me = False  # flag: include macro expansions in listing
        # macro vars as well
        self.mcount = 1  # nonce for macros
        self.mcalls = 0  # the number of macro expansions made so far
        self.macdef = False
        self.mname = ""
        self.marity = 0
        self.mvars: Dict[str, str] = {}
        self.macros: Dict[str, List[str]] = {}
        self.mstack: List[List[str]] = [[], [], [], [], [], []]
        self.pars: List[str] = []


# Used by CocoIDE when imported
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

iset: Dict[str, Tuple[int, int]] = {
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
}


class CocAs(tk.Tk):
    def __init__(self, master=None) -> None:
        self.master = master
        self.mainWin = tk.Toplevel(master=master)
        self.mainWin.lift()
        self.mainWin.resizable(width=False, height=False)
        self.mainWin.title("CDM8 Assembler: CocAs GUI")
        if __name__ == "__main__":
            self.mainWin.protocol(
                "WM_DELETE_WINDOW", self.closeCocas
            )  # Only if main module
        self.mainWin.focus()
        ## Create buttonbar, link and status panels
        buttonBar = ttk.Frame(
            self.mainWin, name="buttonbar", height=35, width=400, border=2
        )
        buttonBar.pack(side=tk.TOP, fill=tk.X, expand=False)

        linkPanel = ttk.Frame(self.mainWin, name="link", border=2, relief="sunken")
        linkPanel.pack(side=tk.TOP, fill=tk.X, expand=1)
        self.linkText = ttk.Label(linkPanel, text="No file selected")
        self.linkText.pack(expand=1)
        self.linkText.bind("<Key>", lambda e: "break")

        seperator = ttk.Frame(self.mainWin, name="sep1", height=35, border=2)
        seperator.pack(side=tk.TOP, fill=tk.BOTH, expand=False)

        statusPanel = ttk.Frame(self.mainWin, name="status", border=2, relief="sunken")
        statusPanel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.statusText = sctx.ScrolledText(statusPanel, height=25, wrap=tk.NONE)
        self.statusText.pack(fill=tk.BOTH, expand=1)
        self.statusText.bind("<Key>", lambda e: "break")

        # buttons
        addButton = ttk.Button(buttonBar, text="Select .asm File", command=self.addFile)
        addButton.pack(side=tk.LEFT)
        linkButton = ttk.Button(
            buttonBar,
            text="Assemble to .obj File",
            command=self.asmFile,
        )
        linkButton.pack(side=tk.LEFT)
        quitButton = ttk.Button(buttonBar, text="Quit", command=self.closeCocas)
        quitButton.pack(side=tk.LEFT)

        self.asmfile = ""

    def addFile(self, event=None) -> None:
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
            self.linkText.config(text=filepath + "\n")
            self.statusText.delete("1.0", tk.END)

    def asmFile(self, event=None) -> None:
        error_msg = ""

        ctx = Context()
        ctx.lst = True

        self.statusText.delete("1.0", tk.END)
        if not self.asmfile:
            error_msg = "No file to Assemble!\n"
        else:
            if self.asmfile[-4:] == ".asm":
                filename = self.asmfile[:-4]
                try:
                    fileBuff = open("{}.asm".format(filename), "r")
                except IOError:
                    error_msg = "{}.asm: file not found".format(filename)
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
                "\n\nASSEMBLED OK! Written to:\n {}.obj\n".format(self.asmfile[:-4]),
            )
            self.statusText.insert(tk.END, "\nASSEMBLER REPORT LISTING:\n" + codelist)
            self.statusText.insert(tk.END, "\nOBJECT CODE:\n")
            self.statusText.insert(tk.END, obj_code)
            self.statusText.see(tk.END)
            # print("**", obj_code) # debug
        # Save obj file
        # print("Saving obj file")
        try:
            with io.open("{}.obj".format(filename), "w", encoding="utf8") as f:
                f.write(obj_code)
            print()
        except TypeError:
            raise
            error_msg = "TypeError"
            # return "break"
        except Exception as e:
            error_msg = str(e)
            # return "break"
        if error_msg:
            self.statusText.insert(tk.END, error_msg)
        else:
            self.statusText.insert(tk.END, "\nSaved OBJ:\n {}.obj OK".format(filename))
        self.statusText.see(tk.END)

    def closeCocas(self) -> None:
        self.mainWin.destroy()
        if __name__ == "__main__":
            self.master.destroy()  # type: ignore


class AssemblerError:
    def __init__(self, ctx: Context, line: int, col: int, message: str) -> None:
        self.ctx = ctx
        self.line = line
        self.col = col
        self.message = message

    def dump(self) -> None:
        if self.col >= 0:
            source = "{}\n{}^".format(
                self.ctx.raw_text[self.line - 1], " " * (self.col + 1)
            )
        else:
            source = self.ctx.raw_text[self.line - 1]
        print(
            "On line {} \n{}\nERROR: {}".format(
                self.line,
                source,
                self.message,
            )
        )


class LexerError(AssemblerError):
    def __init__(self, ctx: Context, line: int, col: int, message: str) -> None:
        super().__init__(ctx, line, col, message)


class SyntaxError(AssemblerError):
    def __init__(self, ctx: Context, line: int, col: int, message: str) -> None:
        super().__init__(ctx, line, col, message)


class MacroError(AssemblerError):
    def __init__(
        self,
        ctx: Context,
        line: int,
        col: int,
        message: str,
        user_message: bool = False,
    ) -> None:
        super().__init__(ctx, line, col, message)
        self.user_message = user_message

    def dump(self) -> None:
        if self.col >= 0:
            source = "{}\n{}^".format(
                self.ctx.raw_text[self.line - 1], " " * (self.col + 1)
            )
        else:
            source = self.ctx.raw_text[self.line - 1]
        if self.user_message:
            print(
                "On line {} \n{}\nERROR: {}".format(
                    self.line,
                    source,
                    self.message,
                )
            )
        else:
            print(
                "On line {} \n{}\nERROR: In Macro: {}".format(
                    self.line,
                    source,
                    self.message,
                )
            )


class TokenType(Enum):
    EMPTY = auto()
    ID = auto()
    NUM = auto()
    COLON = auto()
    COMMA = auto()
    PLUS = auto()
    MINUS = auto()
    GREATER = auto()
    SOLIDUS = auto()
    APOSTROPHE = auto()
    QUESTION = auto()
    EXCLAMATION = auto()
    DOT = auto()
    EQUAL = auto()
    STR = auto()
    PAR = auto()  # Macro Parameter
    REG = auto()
    END = auto()


CHAR_KINDS = {
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    ">": TokenType.GREATER,
    "/": TokenType.SOLIDUS,
    "'": TokenType.APOSTROPHE,
    "?": TokenType.QUESTION,
    "!": TokenType.EXCLAMATION,
    ".": TokenType.DOT,
    "=": TokenType.EQUAL,
}


class Token:
    kind: TokenType
    ind: int = -1
    value: Union[str, int] = 0

    def __init__(
        self, kind: TokenType, ind: int = -1, value: Union[str, int] = 0
    ) -> None:
        self.kind = kind
        self.ind = ind
        self.value = value


def lex(ctx: Context, s: str, line: int, col: int) -> Union[AssemblerError, Token]:
    def hexbyte(s: str) -> int:
        w = s
        w = w.lower()
        k = "0123456789abcdef".find(w[0])
        m = "0123456789abcdef".find(w[1])
        if m < 0 or k < 0:
            return -1
        return 16 * k + m

    ln = len(s)
    if ln == 0:
        return Token(TokenType.EMPTY)
    i = 0
    while s[i] == " " or s[i] == "\t" or s[i] == "#":
        if i == ln - 1 or s[i] == "#":
            return Token(TokenType.EMPTY)
        else:
            i = i + 1
    x = s[i]
    if x.isalpha() or x == "_" or x == "*":
        kind = TokenType.ID
    elif x.isdigit():
        kind = TokenType.NUM
    elif x in CHAR_KINDS:
        kind = CHAR_KINDS[x]
    elif x == '"':
        kind = TokenType.STR
    elif x == "$":
        kind = TokenType.PAR
    else:
        return LexerError(ctx, line, col, "Illegal character ‘{}’".format(x))

    if kind is TokenType.ID:
        value = ""
        if x == "*":
            value = x
            i = i + 1
        while x.isalnum() or x == "_":
            value += x
            if i == ln - 1:
                i = -1
                break
            i = i + 1
            x = s[i]
        if len(value) == 1:
            return Token(kind, i, value)
        if (value[0] == "r" or value[0] == "R") and value[1].isdigit():
            kind = TokenType.REG
            reg = int(value[1])
            if reg > 3:
                return LexerError(
                    ctx, line, col, "Illegal register number {}".format(reg)
                )
            return Token(kind, i, reg)
        return Token(kind, i, value)
    elif kind is TokenType.PAR:
        if i < ln - 1:
            if not s[i + 1].isdigit():
                return LexerError(ctx, line, col + 1, "Expect a digit after a $")
            return Token(kind, i + 2, int(s[i + 1]))
        return LexerError(ctx, line, col + 1, "Expect a digit after a $")
    elif kind is TokenType.NUM:
        if ln - 1 >= i + 1 and s[i : i + 2] == "0x":
            if ctx.got_minus:
                return LexerError(ctx, line, col, "Signed hexadecimal not allowed")
            if ln - 1 < i + 3:
                return LexerError(ctx, line, col, "Illegal hexadecimal")
            k = hexbyte(s[i + 2 : i + 4])
            if k < 0:
                return LexerError(ctx, line, col, "Illegal hexadecimal")
            if ln - 1 > i + 3:
                return Token(kind, i + 4, k)
            else:
                return Token(kind, -1, k)

        if ln - 1 >= i + 1 and s[i : i + 2] == "0b":
            if ctx.got_minus:
                return LexerError(ctx, line, col, "Signed binary not allowed")
            if ln - 1 < i + 9:
                return LexerError(ctx, line, col, "Illegal binary")
            k = 0
            for x in s[i + 2 : i + 10]:
                if "01".find(x) < 0:
                    return LexerError(ctx, line, col, "Illegal binary")
                k = k * 2 + int(x)
            if ln - 1 > i + 9:
                return Token(kind, i + 10, k)
            else:
                return Token(kind, -1, k)

        k = 0
        ctx.got_minus = False
        while x.isdigit():
            k = 10 * k + int(x)
            if i == ln - 1:
                if k > 255:
                    return LexerError(ctx, line, col, "Decimal out of range")
                return Token(kind, -1, k)
            else:
                i = i + 1
                x = s[i]
        if k > 255:
            return LexerError(ctx, line, col, "Decimal out of range")
        return Token(kind, i, k)
    elif kind is TokenType.STR:
        w = ""
        x = ""
        while x != '"':
            if i == ln - 1:
                return LexerError(ctx, line, col, "Runaway string")
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
                return LexerError(
                    ctx, line, col, "Unknown escape character \\" + s[i + 1]
                )
            x = s[i]
        if i == ln - 1:
            return Token(kind, -1, w)
        else:
            return Token(kind, i + 1, w)

    else:
        if ln == 1:
            i = -1
        else:
            i = i + 1
        if kind is TokenType.MINUS:
            ctx.got_minus = True
        else:
            ctx.got_minus = False
        return Token(kind, i, 0)


def lexline(ctx: Context, linum: int, s: str) -> Union[AssemblerError, List[Token]]:
    ctx.got_minus = False
    r: List[Token] = []
    ind = 0
    ptr = 0
    while ind >= 0:
        res = lex(ctx, s, linum, ptr)
        if isinstance(res, AssemblerError):
            return res
        else:
            cat = res.kind
            ind = res.ind
            val = res.value

        if (cat is TokenType.EMPTY and len(r) == 0) or cat is not TokenType.EMPTY:
            r += [Token(cat, ptr, val)]
        if ind >= 0:
            ptr += ind
        s = s[ind:]
    return r


class Node:
    label: Optional[str] = None


class SizedNode:
    size: int


class MacroNode(Node):
    pass


class MendNode(Node):
    pass


class CodeNode(Node, SizedNode):
    code: List[int]

    def __init__(
        self, label: Optional[str] = None, size: int = 0, code: List[int] = []
    ) -> None:
        self.label = label
        self.size = size
        self.code = code


class ConstantNode(CodeNode):
    def __init__(self, label: Optional[str], code: List[int] = []) -> None:
        super().__init__(label, len(code), code)


class SpaceNode(CodeNode):
    value: List[int]

    def __init__(self, label: Optional[str], size: int) -> None:
        super().__init__(label, size, [0] * size)


class MacroExpandNode(Node):
    value: List[str]

    def __init__(self, value: List[str] = []) -> None:
        self.value = value


class SetNode(Node):
    def __init__(self, label: Optional[str], value: int) -> None:
        self.label = label
        self.value = value


class SectionNode(Node):
    pass


class AsectNode(SectionNode):
    address: int

    def __init__(self, address: int) -> None:
        self.address = address


class TplateNode(SectionNode):
    pass


class RsectNode(SectionNode):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class EndNode(Node):
    pass


class ExtNode(Node):
    def __init__(self, label: str, name: str) -> None:
        self.label = label
        self.name = name


def asmline(
    ctx: Context, s: str, linum: int, passno: int
) -> Union[AssemblerError, Node]:
    def parse_exp(
        lst: List[Token], onlyabs: bool = False
    ) -> Union[Tuple[int, bool], SyntaxError]:
        gotrel = False
        relcontext = ctx.sect_name != "$abs"
        opsynt = [lst[j].kind for j in range(3)]
        if opsynt[0:2] == [TokenType.NUM, TokenType.END]:
            return (int(lst[0].value), gotrel)
        if opsynt[0] is TokenType.ID:
            lbl = str(lst[0].value)
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
                if opsynt[1] is TokenType.COLON:
                    return SyntaxError(ctx, linum, -1, str(lst[2].value))
                return SyntaxError(
                    ctx, linum, lst[0].ind, "Label {} not found".format(lbl)
                )
            if opsynt[1] is TokenType.END or opsynt[1] is TokenType.COLON:
                if onlyabs and gotrel:
                    return SyntaxError(
                        ctx, linum, lst[0].ind, "Only absolute labels allowed here"
                    )
                return (Value, gotrel)
            if opsynt[1] is TokenType.PLUS:
                sign = 1
            elif opsynt[1] is TokenType.MINUS:
                sign = -1
            else:
                return SyntaxError(ctx, linum, lst[1].ind, "Only + or - allowed here")
            # extension for NSU ######################

            if opsynt[2] is TokenType.ID:
                lbl2 = str(lst[2].value)
                if lbl2 in ctx.exts:
                    return SyntaxError(
                        ctx,
                        linum,
                        lst[2].ind,
                        "External label {} can't be used as displacement".format(lbl2),
                    )
                if ctx.sect_name and lbl2 in ctx.labels[ctx.sect_name] or lbl2 == "*":
                    Value2 = (
                        ctx.labels[ctx.sect_name][lbl2]
                        if ctx.sect_name
                        else ctx.counter
                    )
                    if relcontext and lbl2 not in ctx.exts and gotrel:
                        if sign == 1:
                            return SyntaxError(
                                ctx,
                                linum,
                                lst[2].ind,
                                "Relocatables can only be subtracted",
                            )
                        else:
                            gotrel = False  # difference between two relocs
                    if gotrel and onlyabs:
                        return SyntaxError(
                            ctx,
                            linum,
                            lst[0].ind,
                            "Only absolute result is acceptable here",
                        )
                    return (((Value + sign * Value2) + 256) % 256, gotrel)
                if lbl2 in ctx.abses:
                    if gotrel and onlyabs:
                        return SyntaxError(
                            ctx,
                            linum,
                            lst[0].ind,
                            "Only absolute result is acceptable here",
                        )
                    Value2 = ctx.abses[lbl2]
                    return (((Value + sign * Value2) + 256) % 256, gotrel)
                return SyntaxError(
                    ctx, linum, lst[2].ind, "Label {} not found".format(lbl2)
                )

            ########################################
            elif opsynt[2] is TokenType.NUM:
                if onlyabs and gotrel:
                    return SyntaxError(
                        ctx, linum, lst[0].ind, "Only absolute labels allowed here"
                    )
                return (((Value + sign * int(lst[2].value)) + 256) % 256, gotrel)
            else:
                return SyntaxError(
                    ctx, linum, lst[2].ind, "Expecting a number or a label here"
                )
        elif opsynt[0:3] == [TokenType.MINUS, TokenType.NUM, TokenType.END]:
            value = int(lst[1].value)
            if value > 128:
                return SyntaxError(ctx, linum, lst[1].ind, "Negative out of range")
            return (((value ^ 0xFF) + 1) % 256, gotrel)
        else:
            return SyntaxError(ctx, linum, lst[0].ind, "Label or number expected")

    lex_res = lexline(ctx, linum, s)
    if isinstance(lex_res, AssemblerError):
        return lex_res
    cmd = lex_res + [Token(TokenType.END, 0)] * 3
    if cmd[0].kind is TokenType.EMPTY:
        return CodeNode()
    if cmd[0].kind is not TokenType.ID:
        return SyntaxError(ctx, linum, cmd[0].ind, "Label or opcode expected")
    else:
        next = 1
        label = None
        opcode = str(cmd[0].value)
        pos = cmd[0].ind
        if cmd[1].kind is TokenType.COLON or cmd[1].kind is TokenType.GREATER:
            if cmd[2].kind is TokenType.ID or cmd[2].kind is TokenType.END:
                next = 3
                if cmd[1].kind is TokenType.COLON:
                    label = str(cmd[0].value)
                else:
                    label = ">" + str(cmd[0].value)
                opcode = str(cmd[2].value)
                pos = cmd[2].ind
                if cmd[2].kind is TokenType.END:
                    return CodeNode(label)
            else:
                return SyntaxError(ctx, linum, cmd[2].ind, "Illegal opcode")
        if opcode not in iset:
            return SyntaxError(ctx, linum, pos, "Invalid opcode: " + opcode)
        (bincode, cat) = iset[opcode]
        if cat == bi:
            if cmd[next].kind is not TokenType.REG:
                return SyntaxError(ctx, linum, cmd[next].ind, "Register expected")
            if cmd[next + 1].kind is not TokenType.COMMA:
                return SyntaxError(ctx, linum, cmd[next + 1].ind, "Comma expected")
            if cmd[next + 2].kind is not TokenType.REG:
                return SyntaxError(ctx, linum, cmd[next + 2].ind, "Register expected")
            if cmd[next + 3].kind is not TokenType.END:
                return SyntaxError(ctx, linum, cmd[next + 3].ind, "Unexpected text")
            x = bincode + 4 * int(cmd[next].value) + int(cmd[next + 2].value)
            return CodeNode(label, 1, [x])
        if cat == un:
            if opcode in ("ldsa", "addsp", "setsp", "pushall", "popall") and ctx.v3:
                return SyntaxError(
                    ctx,
                    linum,
                    cmd[next].ind,
                    "option -v3 forbids use of Mark 4 instructions",
                )

            if cmd[next].kind is not TokenType.REG:
                return SyntaxError(ctx, linum, cmd[next].ind, "Register expected")
            x = bincode + int(cmd[next].value)
            if opcode == "ldi" or opcode == "ldsa":
                if cmd[next + 1].kind is not TokenType.COMMA:
                    return SyntaxError(ctx, linum, cmd[next + 1].ind, "Comma expected")
                if passno == 1:
                    return CodeNode(label, 2, [x, 0])
                elif cmd[next + 2].kind is TokenType.STR:
                    strVal = str(cmd[next + 2].value)
                    if len(strVal) > 1:
                        return SyntaxError(
                            ctx, linum, cmd[next + 2].ind, "Single character expected"
                        )
                    if opcode == "ldsa":
                        return SyntaxError(
                            ctx,
                            linum,
                            cmd[next + 2].ind,
                            "ldsa requires a number or a template field",
                        )
                    return CodeNode(label, 2, [x, ord(strVal[0])])
                elif cmd[next + 3].kind is TokenType.DOT:  # template reference
                    if cmd[next + 2].kind is not TokenType.ID:
                        return SyntaxError(
                            ctx, linum, cmd[next + 2].ind, "Template name expected"
                        )
                    if cmd[next + 2].value not in ctx.tpls:
                        return SyntaxError(
                            ctx, linum, cmd[next + 2].ind, "Unknown template"
                        )
                    tn = str(cmd[next + 2].value)
                    if cmd[next + 4].kind is not TokenType.ID:
                        return SyntaxError(
                            ctx, linum, cmd[next + 4].ind, "Field name expected"
                        )
                    if cmd[next + 4].value not in ctx.tpls[tn]:
                        return SyntaxError(
                            ctx, linum, cmd[next + 4].ind, "Unknown field name"
                        )
                    if cmd[next + 5].kind is not TokenType.END:
                        return SyntaxError(
                            ctx,
                            linum,
                            cmd[next + 5].ind,
                            "unexpected token after template field",
                        )
                    y = ctx.tpls[tn][str(cmd[next + 4].value)]
                    return CodeNode(label, 2, [x, y])
                else:
                    res = parse_exp(cmd[next + 2 : next + 5])
                    if isinstance(res, AssemblerError):
                        return res
                    Value, gotrel = res
                    if cmd[next + 5].kind is not TokenType.END:
                        return SyntaxError(
                            ctx, linum, cmd[next + 5].ind, "Unexpected text"
                        )
                    if ctx.rel and gotrel:
                        if not ctx.sect_name:
                            return SyntaxError(
                                ctx,
                                linum,
                                cmd[next].ind,
                                "Internal: In rsect yet no name",
                            )
                        ctx.rel_list[ctx.sect_name] += [ctx.counter + 1]
                    if (
                        cmd[next + 2].kind is TokenType.ID
                        and cmd[next + 2].value in ctx.exts
                        and not ctx.macdef
                    ):
                        ctx.exts[str(cmd[next + 2].value)] += [
                            (ctx.sect_name, ctx.counter + 1)
                        ]
                    return CodeNode(label, 2, [x, Value])
            else:
                if cmd[next + 1].kind is not TokenType.END:
                    return SyntaxError(
                        ctx, linum, cmd[next + 1].ind, "Only one operand expected"
                    )
                return CodeNode(label, 1, [x])

        if cat == br:
            if passno == 1:
                if opcode == "lchk":
                    return CodeNode(label, 0, [])
                return CodeNode(label, 2, [bincode, 0])
            else:
                if opcode == "ldsa" and cmd[next + 2].kind not in (
                    TokenType.NUM,
                    TokenType.MINUS,
                ):
                    return SyntaxError(
                        ctx,
                        linum,
                        cmd[next + 2].ind,
                        "ldsa requires a number or a template field",
                    )
                res = parse_exp(cmd[next : next + 3])
                if isinstance(res, AssemblerError):
                    return res
                Value, gotrel = res
                if cmd[next + 3].kind is not TokenType.END:
                    return SyntaxError(ctx, linum, cmd[next + 3].ind, "Unexpected text")
                if ctx.rel and opcode != "lchk" and gotrel:
                    if not ctx.sect_name:
                        return SyntaxError(
                            ctx, linum, cmd[next].ind, "Internal: In rsect yet no name"
                        )
                    ctx.rel_list[ctx.sect_name] += [ctx.counter + 1]
                if (
                    cmd[next].kind is TokenType.ID
                    and cmd[next].value in ctx.exts
                    and not ctx.macdef
                ):
                    ctx.exts[str(cmd[next].value)] += [(ctx.sect_name, ctx.counter + 1)]
                if opcode == "lchk":
                    return CodeNode(label, 0, [])
                return CodeNode(label, 2, [bincode, Value])
        if cat == osix:
            if cmd[next].kind is not TokenType.NUM:
                return SyntaxError(ctx, linum, cmd[next].ind, "Number expected")
            if cmd[next + 1].kind is not TokenType.END:
                return SyntaxError(ctx, linum, cmd[next + 1].ind, "Unexpected text")
            return CodeNode(label, 2, [bincode, int(cmd[next].value)])

        if cat == zer:
            return CodeNode(label, 1, [bincode])

        if cat == spmove:  # addsp/setsp
            if passno == 1:
                return CodeNode(label, 2, [0, 0])
            mynext = next
            mymult = 1
            if cmd[mynext].kind is TokenType.MINUS:
                mynext = next + 1
                mymult = -1
            if cmd[mynext].kind is TokenType.NUM:
                if cmd[mynext + 1].kind is not TokenType.END:
                    return SyntaxError(
                        ctx, linum, cmd[mynext + 1].ind, "Unexpected text"
                    )
                return CodeNode(label, 2, [bincode, mymult * int(cmd[mynext].value)])

            if (
                cmd[mynext].kind is not TokenType.ID
                or cmd[mynext + 1].kind is not TokenType.DOT
                or cmd[mynext + 2].kind is not TokenType.ID
            ):
                return SyntaxError(
                    ctx,
                    linum,
                    cmd[mynext].ind,
                    "addsp/setsp instructions require a number or a template field operand",
                )
            if cmd[mynext].value not in ctx.tpls:
                return SyntaxError(
                    ctx,
                    linum,
                    cmd[mynext].ind,
                    "Unknown template '{}'".format(cmd[mynext].value),
                )
            if cmd[mynext + 3].kind is not TokenType.END:
                return SyntaxError(ctx, linum, cmd[mynext + 3].ind, "Unexpected text")

            tn = str(cmd[mynext].value)
            return CodeNode(
                label,
                2,
                [bincode, mymult * ctx.tpls[tn][str(cmd[mynext + 2].value)]],
            )

        ################################################## M A C R O FACILITIES
        if cat == mc:
            if opcode == "macro":
                if ctx.macdef:
                    return MacroNode()
                if label:
                    return SyntaxError(ctx, linum, 0, "Label not allowed")
                if cmd[next].kind is not TokenType.ID:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Name expected")
                ctx.mname = str(cmd[next].value)
                if ctx.mname in iset:
                    if iset[ctx.mname][1] != mi:
                        return SyntaxError(
                            ctx,
                            linum,
                            cmd[next].ind,
                            "Opcode '{}' reserved by assembler".format(ctx.mname),
                        )
                if cmd[next + 1].kind is not TokenType.SOLIDUS:
                    return SyntaxError(ctx, linum, cmd[next + 1].ind, "/ expected")
                if cmd[next + 2].kind is not TokenType.NUM:
                    return SyntaxError(ctx, linum, cmd[next + 2].ind, "Number expected")
                if cmd[next + 3].kind is not TokenType.END:
                    return SyntaxError(ctx, linum, cmd[next + 3].ind, "Unexpected text")
                ctx.marity = int(cmd[next + 2].value)
                return MacroNode()
            elif opcode == "mend":
                if cmd[next].kind is not TokenType.END:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Unexpected text")
                return MendNode()
        if cat == mi:
            if passno == 2 or ctx.macdef:
                return CodeNode()
            ctx.mcalls += 1
            if ctx.mcalls > 800:
                return SyntaxError(ctx, linum, 0, "Too many macro expansions [>800]")
            sep_res = commasep(ctx, linum, cmd[next:])
            if isinstance(sep_res, AssemblerError):
                return sep_res
            ctx.pars = sep_res
            parno = len(ctx.pars)
            if "{}/{}".format(opcode, parno) not in ctx.macros:
                return SyntaxError(
                    ctx,
                    linum,
                    cmd[next].ind,
                    "Number of params ({})does not match definition of macro {}".format(
                        parno, opcode
                    ),
                )

            if not label:
                ll = []
            elif label[0] == ">":
                ll = [label[1:] + ">"]
            else:
                ll = [label + ":"]

            mbody = (
                ["# >>>>>>"]
                + ll
                + ctx.macros["{}/{}".format(opcode, parno)]
                + ["# <<<<<<"]
            )
            newbody: List[str] = []
            for s1 in mbody:
                if ctx.dbg:
                    print(
                        "before => {} ******* pars= {}mvars={}".format(
                            s1, ctx.pars, ctx.mvars
                        )
                    )
                rslt = mxpand(ctx, linum, s1, 0, parno)
                if isinstance(rslt, AssemblerError):
                    return rslt
                if ctx.dbg:
                    print("after  => {}".format(rslt))
                m_res = ismstack(ctx, linum, rslt)
                if isinstance(m_res, AssemblerError):
                    return m_res
                if not m_res:
                    newbody += ["{}#{}".format(rslt, chr(1))]
            ctx.mcount += 1
            return MacroExpandNode(newbody)
        ################################################## END OF MACRO FACILITIES

        if ctx.macdef:
            return CodeNode()
        if cat == spec:
            if opcode == "ds":
                res = parse_exp(cmd[next : next + 3], onlyabs=True)
                if isinstance(res, AssemblerError):
                    return res
                size, _ = res
                ctx.ds_ins = True
                return SpaceNode(label, size)
            if opcode == "set":
                if cmd[next].kind is not TokenType.ID:
                    return SyntaxError(
                        ctx, linum, cmd[next + 1].ind, "Identifier expected"
                    )
                if cmd[next + 1].kind is not TokenType.EQUAL:
                    return SyntaxError(ctx, linum, cmd[next + 1].ind, "'=' expected")
                res = parse_exp(cmd[next + 2 : next + 5], onlyabs=True)
                if isinstance(res, AssemblerError):
                    return res
                value, _ = res
                if passno == 2:
                    return SetNode(label, value)
                alias = str(cmd[next].value)
                if alias in ctx.abses:
                    return SyntaxError(
                        ctx,
                        linum,
                        cmd[next + 1].ind,
                        "{} already defined".format(alias),
                    )
                ctx.abses[alias] = value
                return SetNode(label, value)
            if opcode == "dc":
                img: List[int] = []
                empty = True
                ctx.ds_ins = True
                while cmd[next].kind is not TokenType.END:
                    empty = False
                    if cmd[next].kind is TokenType.NUM:
                        img += [int(cmd[next].value)]
                    elif (
                        cmd[next].kind is TokenType.MINUS
                        and cmd[next + 1].kind is TokenType.NUM
                    ):
                        value = int(cmd[next + 1].value)
                        if value > 128:
                            return SyntaxError(
                                ctx, linum, cmd[next + 1].ind, "Negative out of range"
                            )
                        img += [((value ^ 255) + 1) % 256]
                        next += 1
                    elif cmd[next].kind is TokenType.STR:
                        for c in str(cmd[next].value):
                            img += [ord(c)]
                    elif cmd[next].kind is TokenType.ID:
                        if passno == 1:
                            img += [0]
                            if (
                                cmd[next + 1].kind is TokenType.PLUS
                                or cmd[next + 1].kind is TokenType.MINUS
                            ):
                                next += 2
                        else:
                            exp = cmd[next : next + 3]
                            res = parse_exp(
                                [
                                    x
                                    if x.kind is not TokenType.COMMA
                                    else Token(TokenType.END, 0)
                                    for x in exp
                                ]
                            )
                            if isinstance(res, AssemblerError):
                                return res
                            Value, gotrel = res
                            if ctx.rel and gotrel:
                                if not ctx.sect_name:
                                    return SyntaxError(
                                        ctx,
                                        linum,
                                        cmd[next].ind,
                                        "Internal: In rsect yet no name",
                                    )
                                ctx.rel_list[ctx.sect_name] += [ctx.counter + len(img)]
                            if (
                                cmd[next].kind is TokenType.ID
                                and cmd[next].value in ctx.exts
                                and not ctx.macdef
                            ):
                                ctx.exts[str(cmd[next].value)] += [
                                    (ctx.sect_name, ctx.counter + len(img))
                                ]

                            img += [Value]

                            if (
                                cmd[next + 1].kind is TokenType.PLUS
                                or cmd[next + 1].kind is TokenType.MINUS
                            ):
                                next += 2

                    else:
                        return SyntaxError(
                            ctx, linum, cmd[next].ind, "Illegal constant"
                        )

                    if cmd[next + 1].kind is TokenType.COMMA:
                        empty = True
                        next += 2
                    elif cmd[next + 1].kind is not TokenType.END:
                        return SyntaxError(
                            ctx, linum, cmd[next + 1].ind, "Illegal separator"
                        )
                    else:
                        return ConstantNode(label, img)
                if empty:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Data expected")

            if opcode == "asect":
                if label:
                    return SyntaxError(ctx, linum, 0, "Label not allowed")
                if cmd[next].kind is not TokenType.NUM:
                    return SyntaxError(
                        ctx, linum, cmd[next].ind, "Numerical address expected"
                    )
                addr = int(cmd[next].value)
                if addr < 0:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Illegal number")
                if cmd[next + 1].kind is not TokenType.END:
                    return SyntaxError(ctx, linum, cmd[next + 1].ind, "Unexpected text")
                if ctx.rel:
                    if not ctx.sect_name:
                        return SyntaxError(
                            ctx, linum, cmd[next].ind, "Internal: In rsect yet no name"
                        )
                    ctx.rsects[ctx.sect_name] = ctx.counter
                    ctx.rel = False
                if ctx.tpl:
                    ctx.tpl = False
                    ctx.tpls[ctx.tpl_name]["_"] = ctx.counter
                ctx.counter = addr
                ctx.sect_name = "$abs"
                return AsectNode(addr)
            if opcode == "tplate":
                if label:
                    return SyntaxError(ctx, linum, 0, "Label not allowed")
                if cmd[next].kind is not TokenType.ID:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Name expected")
                if ctx.rel:
                    if not ctx.sect_name:
                        return SyntaxError(
                            ctx, linum, cmd[next].ind, "Internal: In rsect yet no name"
                        )
                    ctx.rsects[ctx.sect_name] = ctx.counter
                ctx.rel = False
                if cmd[next].value in ctx.tpls and passno == 1:
                    return SyntaxError(
                        ctx, linum, cmd[next].ind, "Template already defined"
                    )
                ctx.counter = 0
                ctx.tpl = True
                ctx.tpl_name = str(cmd[next].value)
                if ctx.tpl_name not in ctx.tpls:
                    ctx.tpls[ctx.tpl_name] = {}
                ctx.sect_name = None
                return TplateNode()
            if opcode == "rsect":
                if label:
                    return SyntaxError(ctx, linum, 0, "Label not allowed")
                if cmd[next].kind is not TokenType.ID:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Name expected")
                if cmd[next + 1].kind is not TokenType.END:
                    return SyntaxError(ctx, linum, cmd[next + 1].ind, "Unexpected text")
                if ctx.rel:
                    if not ctx.sect_name:
                        return SyntaxError(
                            ctx, linum, cmd[next].ind, "Internal: In rsect yet no name"
                        )
                    ctx.rsects[ctx.sect_name] = ctx.counter
                ctx.rel = True
                if ctx.tpl:
                    ctx.tpl = False
                    ctx.tpls[ctx.tpl_name]["_"] = ctx.counter
                ctx.sect_name = str(cmd[next].value)
                if ctx.sect_name not in ctx.rsects:
                    ctx.rsects[ctx.sect_name] = 0
                    ctx.counter = 0
                    ctx.labels[ctx.sect_name] = {}
                    ctx.ents[ctx.sect_name] = {}
                    ctx.rel_list[ctx.sect_name] = []
                else:
                    ctx.counter = ctx.rsects[ctx.sect_name]
                return RsectNode(ctx.sect_name)
            if opcode == "ext":
                if cmd[next].kind is not TokenType.END:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Unexpected text")
                if not label:
                    return SyntaxError(ctx, linum, cmd[next].ind, "Should be labeled")
                if not ctx.sect_name:
                    return SyntaxError(
                        ctx, linum, cmd[next].ind, "Internal: ext yet no section name"
                    )
                if label not in ctx.exts or label not in ctx.labels[ctx.sect_name]:
                    ctx.exts[label] = []
                    return ExtNode("!" + label, str(cmd[next].value))
                return CodeNode()
            if opcode == "end":
                if label:
                    return SyntaxError(ctx, linum, 0, "Illegal label")
                if ctx.rel:
                    if not ctx.sect_name:
                        return SyntaxError(
                            ctx, linum, cmd[next].ind, "Internal: In rsect yet no name"
                        )
                    ctx.rsects[ctx.sect_name] = ctx.counter
                if passno == 1:
                    if ctx.tpl:
                        ctx.tpls[ctx.tpl_name]["_"] = ctx.counter
                        ctx.tpl = False
                    for name in ctx.rsects:
                        ctx.rsects[name] = 0
                ctx.rel = False
                return EndNode()
        else:
            return SyntaxError(
                ctx, linum, 0, "Internal error: {} {}{}".format(opcode, cat, linum)
            )


def asm(
    ctx: Context, assmtext: Optional[List[str]] = None
) -> Union[AssemblerError, List[Tuple[int, int, List[int], str]]]:
    if assmtext is not None:
        ctx.text = assmtext

    output: List[Tuple[int, int, List[int], str]] = []
    ctx.generated = len(ctx.text) * [False]
    for passno in [1, 2]:
        linum = 0
        linind = 0
        ready = False
        finished = False

        while True:
            if linind <= len(ctx.text) - 1:
                s = ctx.text[linind]
                if not ctx.generated[linind]:
                    linum += 1
                linind += 1
            else:
                break

            res = asmline(ctx, s, linum, passno)
            if isinstance(res, AssemblerError):
                if not ctx.macdef or not isinstance(res, SyntaxError):
                    return res

            if (
                ctx.macdef
                and not isinstance(res, MendNode)
                and not isinstance(res, MacroNode)
            ):  # accumulate macro definition
                if passno == 1:
                    mbody += [s]
                continue
            if isinstance(res, SectionNode):  # sects
                ready = True
                continue
            elif isinstance(res, EndNode):
                if ctx.macdef:
                    return SyntaxError(
                        ctx,
                        linum,
                        -1,
                        "ERROR: 'end' encountered while processing macro definition",
                    )
                finished = True
                break
            elif isinstance(res, MacroNode):  # macro
                if ctx.macdef:
                    return SyntaxError(
                        ctx, linum, -1, "ERROR: macro definition inside macro"
                    )
                ctx.macdef = True
                mbody: List[str] = []
                continue
            elif isinstance(res, MendNode):  # mend
                if not ctx.macdef:
                    return SyntaxError(ctx, linum, -1, "ERROR: mend before macro")
                ctx.macdef = False
                if passno == 1:
                    ctx.macros["{}/{}".format(ctx.mname, ctx.marity)] = mbody
                    iset[ctx.mname] = (0, mi)
                continue
            elif isinstance(res, MacroExpandNode):  # macro expansion
                ctx.text = ctx.text[0:linind] + res.value + ctx.text[linind:]
                ctx.generated = (
                    ctx.generated[0:linind]
                    + len(res.value) * [True]
                    + ctx.generated[linind:]
                )
                continue
            elif isinstance(res, SetNode):  # set
                if passno == 2:
                    output += [
                        (linind, res.value, [], "")
                    ]  # dummy output to get addresses in listing
                continue
            else:  # deal with the label off a true instruction
                if ctx.tpl and passno == 1:
                    if not ctx.ds_ins and isinstance(res, SizedNode) and res.size > 0:
                        return SyntaxError(
                            ctx,
                            linum,
                            -1,
                            "On line {} ERROR: Only dc/ds allowed in templates".format(
                                linum
                            ),
                        )
                    ctx.ds_ins = False
                if isinstance(res, Node) and res.label and passno == 1:
                    if not ready:
                        return SyntaxError(
                            ctx,
                            linum,
                            -1,
                            "On line {} ERROR: 'asect' or 'rsect' expected".format(
                                linum
                            ),
                        )
                    addr = ctx.counter
                    if ctx.tpl:
                        if res.label[0] == ">":
                            return SyntaxError(
                                ctx,
                                linum,
                                -1,
                                "On line {} ERROR: exts in template not allowed".format(
                                    linum
                                ),
                            )
                        if res.label in ctx.tpls[ctx.tpl_name]:
                            return SyntaxError(
                                ctx,
                                linum,
                                -1,
                                "On line {} ERROR: Label ‘{}’ already defined".format(
                                    linum, res.label
                                ),
                            )
                        ctx.tpls[ctx.tpl_name][res.label] = ctx.counter
                    if res.label[0] == ">":
                        label = res.label[1:]
                        ctx.ents[ctx.sect_name][label] = ctx.counter
                    if res.label[0] == "!":
                        if res.label[1] == ">":
                            return SyntaxError(
                                ctx,
                                linum,
                                -1,
                                "On line {} ERROR: Label ‘{}’ both ext and entry".format(
                                    linum, label[2:]
                                ),
                            )
                        label = res.label[1:]
                        addr = 0
                    if not ctx.tpl and res.label in ctx.labels[ctx.sect_name]:
                        return SyntaxError(
                            ctx,
                            linum,
                            -1,
                            "On line {} ERROR: Label ‘{}’ already defined".format(
                                linum, res.label
                            ),
                        )
                    if not ctx.tpl:
                        ctx.labels[ctx.sect_name][res.label] = addr
                    if not ctx.rel:
                        ctx.abses[res.label] = ctx.counter

            if (
                passno == 2
                and isinstance(res, CodeNode)
                and res.size > 0
                and not ctx.tpl
            ):
                if not ready or not ctx.sect_name:
                    return SyntaxError(
                        ctx,
                        linum,
                        -1,
                        "On line {} ERROR: 'asect' or 'rsect' expected".format(linum),
                    )
                output += [(linind, ctx.counter, res.code, ctx.sect_name)]
            if passno == 2 and ctx.tpl:
                output += [
                    (linind, ctx.counter, [], "")
                ]  # dummy output to get addresses in listing
            if isinstance(res, SizedNode) and res.size > 0:
                ctx.counter += res.size
        if not finished:
            return SyntaxError(ctx, linum, 0, "ERROR: file ends before end of program")
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

    if prtOP:
        print(
            "\nCdM-8 Assembler v{} <<<{}.asm>>> {} {}\n".format(
                ASM_VER,
                ctx.filename,
                time.strftime("%d/%m/%Y"),
                time.strftime("%H:%M:%S"),
            )
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
                if prtOP:
                    print(
                        "{} {:3d}  {}".format(" " * offset, ln, s)
                    )  # just print the mi
                else:
                    retlist += "{} {:3d}{}\n".format(" " * offset, ln, s)

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
                        if prtOP:
                            print(
                                "{} {:3d}  {}".format(
                                    ("<scattered>" + " " * offset)[0:offset], ln, s
                                )
                            )
                        else:
                            retlist += "{} {:3d}\n".format(
                                ("<scattered>" + " " * offset)[0:offset], ln
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
            if prtOP:
                print("{} {:3d}  {}".format(" " * offset, ln, s))
            else:
                retlist += "{} {:3d}  {}\n".format(" " * offset, ln, s)
        else:
            addr = obj[0][1]
            clist = obj[0][2]
            secname = obj[0][3]
            obj = obj[1:]
            tstr = s
            ln1 = ln
            if secname == "":  # template
                if prtOP:
                    print(
                        "{} {:3d}  {}".format(
                            "{:02x}: {}".format(addr, " " * offset)[0:offset], ln1, s
                        )
                    )
                else:
                    retlist += "{} {:3d}  {}\n".format(
                        "{:02x}: {}".format(addr, " " * offset)[0:offset], ln1, s
                    )
            while clist != []:
                pstr = "{:02x}: {}".format(addr, " ".join(map(shex, clist[0:4])))
                ppr = (pstr + " " * offset)[0:offset]
                if ln1 > 0:
                    sln = format(ln1, "3d")
                else:
                    sln = " "
                if prtOP:
                    print("{} {}  {}".format(ppr, sln, tstr))
                else:
                    retlist += "{} {}  {}\n".format(ppr, sln, tstr)
                if len(clist) <= 4:
                    break
                addr += 4
                tstr = " "
                ln1 = 0
                clist = clist[4:]

    if prtOP:  # Not needed for cocide
        print("\n" + "=" * 70)
        print("\nSECTIONS:\nName\tSize\tRelocation offsets\n")

        for name in ctx.rsects:
            relsn = ctx.rel_list[name]
            strg = ""
            for r in relsn:
                strg += "{:02x} ".format(r)
            print("{}\t{:02x}\n{}".format(name, ctx.rsects[name], strg))

        print("\nENTRIES:\nSection\t\tName/Offset\n")
        for name in ctx.ents:
            strg = "{}\t\t".format(name)
            if ctx.ents[name] == {}:
                strg += "<NONE>"
                print(strg)
                continue
            for nm in ctx.ents[name]:
                strg += "{}:{:02x}\t".format(nm, ctx.ents[name][nm])
            print(strg)

        print("\nEXTERNALS:\nName\t\tUsed in\n")
        for name in ctx.exts:
            strg = "{}\t\t".format(name)
            for nm, oset in ctx.exts[name]:
                strg += "{}+{:02x} ".format(nm, oset)
            print(strg)
        print("\n" + 70 * "=")
    else:
        return retlist


def genoc(
    ctx: Context,
    output: List[Tuple[int, int, List[int], str]],
    objfile: Optional[IO[str]] = None,
) -> Optional[str]:
    def eladj(absegs: List[Tuple[int, List[int]]]) -> List[Tuple[int, List[int]]]:
        if len(absegs) < 2:  # elimenate adjacent segments
            return absegs
        x, y, w = absegs[0], absegs[1], absegs[2:]
        if x[0] + len(x[1]) == y[0]:  # adjacent: merge into one
            return eladj([(x[0], x[1] + y[1])] + w)
        else:
            return [x] + eladj([y] + w)

    if objfile:
        buff = objfile
    else:
        buff = objbuff = io.StringIO()

    sects: Dict[str, List[int]] = {}
    absegs: List[Tuple[int, List[int]]] = []
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
    for a, d in absegs:
        buff.write("ABS  {:02x}: {}\n".format(a, " ".join(map(shex, d))))

    en = ctx.ents["$abs"]
    for e in en:
        buff.write("NTRY {} {}\n".format(e, shex(en[e])))

    for st in sects:
        buff.write("NAME {}\n".format(st))
        buff.write("DATA {}\n".format(" ".join(map(shex, sects[st]))))
        buff.write("REL  {}\n".format(" ".join(map(shex, ctx.rel_list[st]))))
        en = ctx.ents[st]
        for e in en:
            buff.write("NTRY {} {}\n".format(e, shex(en[e])))

    for extn in ctx.exts:
        strg = "XTRN {}:".format(extn)
        if ctx.exts[extn] == []:
            print("WARNING: ext '{}' declared, not used".format(extn))
        for n, offset in ctx.exts[extn]:
            strg += " {} {}".format(n, shex(offset))
        buff.write("{}\n".format(strg))

    if not objfile:
        return objbuff.getvalue()
    return None


def takemdefs(
    ctx: Context, objfile: IO[str], filename: str
) -> Optional[AssemblerError]:
    def formerr() -> MacroError:
        return MacroError(
            ctx,
            ln,
            -1,
            "Error in macro library file ‘{}’ On line {}:\n{}".format(filename, ln, l),
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
                return formerr()
            if not l[1].isalpha():
                return formerr()
            k = 2
            found = False
            while k <= len(l) - 1:
                if not (l[k].isalnum() or l[k] == "_"):
                    found = True
                    break
                k += 1
            if not found:
                return formerr()
            if l[k] != "/":
                return formerr()
            opcode = l[1:k]
            k += 1
            if k > len(l) or not l[k].isdigit():
                return formerr()
            name = l[1 : k + 1]
            body = []
            state = 1
    ctx.macros[name] = body
    iset[opcode] = (0, mi)

    return None


###################### M A C R O  FACILITIES


def mxpand(
    ctx: Context, line: int, s: str, pos: int, pno: int
) -> Union[str, AssemblerError]:
    # substitute factual pars for $1...$<pno> in s escaping quoted strings
    # substitute a nonce for ' and strings for ?<id> from mvars

    if s == "":
        return ""
    if len(s) == 1 and s == "$":
        return SyntaxError(ctx, line, pos, "Missing parameter number")
    x = s[0]

    if x == "$":
        if not s[1].isdigit():
            return SyntaxError(ctx, line, pos, "Illegal parameter number")
        n = int(s[1])
        if n > pno:
            return SyntaxError(ctx, line, pos, "Parameter number too high")
        k = len(ctx.pars[n - 1])
        res = mxpand(ctx, line, s[2:], pos + k - 2, pno)
        if isinstance(res, AssemblerError):
            return res
        return ctx.pars[n - 1] + res

    if x == "?":
        res = mxpand(ctx, line, s[1:], pos + 1, pno)
        if isinstance(res, AssemblerError):
            return res
        return mxpand(ctx, line, "!" + res, pos, pno)
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
            return SyntaxError(
                ctx, line, pos, "Illegal macro-variable '{}'".format(ofc)
            )
        if w not in ctx.mvars:
            return SyntaxError(ctx, line, pos, "Unassigned macro-variable: " + w)
        res = mxpand(ctx, line, s[k:], pos + len(ctx.mvars[w]), pno)
        if isinstance(res, AssemblerError):
            return res
        return ctx.mvars[w] + res

    if x == "'":
        smcount = str(ctx.mcount)
        res = mxpand(ctx, line, s[1:], pos + len(smcount), pno)
        if isinstance(res, AssemblerError):
            return res
        return smcount + res
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
                res = mxpand(ctx, line, s[k + 1 :], pos + k + 1, pno)
                if isinstance(res, AssemblerError):
                    return res
                return s[: k + 1] + res
            k += 1
        return s
    else:
        res = mxpand(ctx, line, s[1:], pos + 1, pno)
        if isinstance(res, AssemblerError):
            return res
        return x + res


def unptoken(ctx: Context, line: int, t: Token) -> Union[AssemblerError, str]:
    if t.kind is TokenType.ID:
        return str(t.value)
    if t.kind is TokenType.REG:
        return "r{}".format(t.value)
    if t.kind is TokenType.NUM:
        return "0x" + format(int(t.value) + 256, "02x")[-2:]
    if t.kind is TokenType.STR:
        return '"{}"'.format((str(t.value).replace("\\", "\\\\")).replace('"', '\\"'))
    return SyntaxError(ctx, line, t.ind, "Illegal item")


def commasep(
    ctx: Context, line: int, tokens: List[Token]
) -> Union[AssemblerError, List[str]]:
    k = 0
    result: List[str] = []
    while k <= len(tokens) - 1:
        if tokens[k].kind is TokenType.END:
            return result
        else:
            if (
                tokens[k].kind is TokenType.ID
                and k <= len(tokens) - 3
                and tokens[k + 1].kind is TokenType.DOT
                and tokens[k + 2].kind is TokenType.ID
            ):  # template field
                a = unptoken(ctx, line, tokens[k])
                if isinstance(a, AssemblerError):
                    return a

                b = unptoken(ctx, line, tokens[k + 2])
                if isinstance(b, AssemblerError):
                    return b

                result += ["{}.{}".format(a, b)]
                k = k + 2
            else:
                a = unptoken(ctx, line, tokens[k])
                if isinstance(a, AssemblerError):
                    return a
                result += [a]
        k = k + 1
        if (
            k <= len(tokens) - 1
            and tokens[k].kind is not TokenType.COMMA
            and tokens[k].kind is not TokenType.END
        ):
            return SyntaxError(ctx, line, tokens[k].ind, "Comma expected here")
        else:
            k = k + 1
    return result


def ismstack(ctx: Context, l: int, s: str) -> Union[AssemblerError, bool]:
    tokens = lexline(ctx, l, s)
    if isinstance(tokens, AssemblerError):
        return tokens

    mstackind = 0
    k = 0

    try:
        if len(tokens) >= 1:
            if tokens[0].kind is TokenType.NUM:
                mstackind = int(tokens[0].value)
                if mstackind > len(ctx.mstack) - 1:
                    if len(tokens) > 1:
                        mstpos = tokens[1].ind
                    else:
                        mstpos = 0
                    return MacroError(
                        ctx, l, mstpos, "Macro stack index too high: " + str(mstackind)
                    )
                tokens = tokens[1:]

        if len(tokens) == 0:
            return False

        if len(tokens) == 1:
            if tokens[0].kind is TokenType.ID and (
                tokens[0].value in ["mpush", "mread", "mpop"]
            ):
                return MacroError(ctx, l, 0, "Macro stack operation without argument")
            else:
                return False

        if (
            len(tokens) >= 3
            and tokens[0].kind is TokenType.ID
            and tokens[1].kind is TokenType.COLON
        ):
            if tokens[2].kind is TokenType.ID and (
                tokens[2].value in ["mpush", "mread", "mpop"]
            ):
                return MacroError(ctx, l, 0, "Macro directives must not be labelled")

        if tokens[0].kind is TokenType.ID and tokens[0].value == "mpush":
            frames = commasep(ctx, l, tokens[1:])
            if isinstance(frames, AssemblerError):
                return frames
            ctx.mstack[mstackind] = frames[::-1] + ctx.mstack[mstackind]
            return True

        if tokens[0].kind is TokenType.ID and (
            tokens[0].value == "mpop" or tokens[0].value == "mread"
        ):
            diagmes = "Macro stack {} empty or too few frames".format(mstackind)
            k = 1
            stoff = 0
            brief = False
            while k < len(tokens):
                if tokens[k].kind is TokenType.ID:
                    if len(ctx.mstack[mstackind]) < stoff + 1:
                        return MacroError(ctx, l, tokens[k].ind, diagmes, brief)
                    if tokens[0].value == "mpop":
                        ctx.mvars[str(tokens[k].value)] = ctx.mstack[mstackind][0]
                        ctx.mstack[mstackind] = ctx.mstack[mstackind][1:]
                    else:
                        ctx.mvars[str(tokens[k].value)] = ctx.mstack[mstackind][stoff]
                        stoff += 1
                elif tokens[k].kind is TokenType.STR:
                    brief = True
                    diagmes = str(tokens[k].value)
                else:
                    return MacroError(
                        ctx,
                        l,
                        tokens[k].ind,
                        "Macro variable or diagnostic message expected here",
                    )
                k += 1
                if k <= len(tokens) - 1 and tokens[k].kind is not TokenType.COMMA:
                    return MacroError(ctx, l, tokens[k].ind, "Comma expected here")
                else:
                    k += 1
            return True

        if (
            tokens[0].kind is TokenType.ID and tokens[0].value == "unique"
        ):  # not a macro stack operation but we keep it here for simplicity
            k = 1
            regfree = 4 * [True]
            regmvars: List[str] = []
            howmany = 0
            while k <= len(tokens) - 1:
                howmany += 1
                if tokens[k].kind is TokenType.ID:
                    regmvars += [str(tokens[k].value)]
                elif tokens[k].kind is TokenType.REG:
                    if regfree[int(tokens[k].value)]:
                        regfree[int(tokens[k].value)] = False
                    else:
                        return MacroError(
                            ctx,
                            l,
                            tokens[k].ind,
                            "r{} occurs more than once".format(tokens[k].value),
                        )
                else:
                    return MacroError(
                        ctx,
                        l,
                        tokens[k].ind,
                        "Macro variable or register expected here",
                    )
                k = k + 1
                if k <= len(tokens) - 1 and tokens[k].kind is not TokenType.COMMA:
                    return MacroError(ctx, l, tokens[k].ind, "Comma expected here")
                else:
                    k = k + 1
            if howmany > 4:
                return MacroError(
                    ctx, l, tokens[0].ind, "More than 4 operands specified"
                )
            for v in regmvars:
                ctx.mvars[v] = ""
            for v in regmvars:
                for k in [0, 1, 2, 3]:
                    if regfree[k]:
                        regfree[k] = False
                        if ctx.mvars[v] != "":
                            return MacroError(
                                ctx,
                                l,
                                tokens[0].ind,
                                "macro var ‘{}’ occurs more than once".format(v),
                            )
                        else:
                            ctx.mvars[v] = "r" + str(k)
                        break
            return True

    except:
        return MacroError(ctx, l, tokens[k].ind, "Macro error!", True)

    return False


################################ E N D OF MACRO FACILITIES


def compile_asm(codetext=None, cdm8ver=4, ctx=None):
    """Entry point when imported as a library"""

    global err_line

    # Init all the global vars

    err_line = None

    ctx = ctx or Context(cdm8ver)

    for line in codetext:
        line = line.rstrip()
        ctx.text += [line.expandtabs()]

    ctx.raw_text = ctx.text.copy()

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
            print("WARNING: no {} found".format(mlb_name))
    if not skipfile:
        res = takemdefs(ctx, mlibfile, mlb_name)
        if isinstance(res, AssemblerError):
            err_line = res.line
            return None, None, res.message
        mlibfile.close()

    result = asm(ctx)
    if isinstance(result, AssemblerError):
        err_line = result.line
        return None, None, result.message

    objstr = genoc(ctx, result)
    if isinstance(objstr, AssemblerError):
        err_line = objstr.line
        return None, None, objstr.message

    codelist = pretty_print(ctx, result, ctx.text, False)
    return objstr, codelist, None


def main() -> None:
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
        root = tk.Tk()
        root.withdraw()
        cocasGUI = CocAs(master=root)
        root.mainloop()
    else:
        ctx = Context()
        ctx.filename = filename
        if filename[-4:] == ".asm":
            filename = filename[:-4]
            ctx.filename = filename
        try:
            asmfile = open("{}.asm".format(filename), "r")
        except IOError:
            print("{}.asm: file not found".format(filename))
            exit(-1)
        for line in asmfile:
            line = line.rstrip()
            ctx.text += [line.expandtabs()]

        ctx.raw_text = ctx.text.copy()

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
                print("WARNING: no {} found".format(mlb_name))

        if not skipfile:
            res = takemdefs(ctx, mlibfile, "standard.mlb")
            if isinstance(res, AssemblerError):
                res.dump()
                exit(-1)
            mlibfile.close()

        if args.mlibs != None:
            for x in args.mlibs:
                if x[-4:] == ".mlb":
                    x = x[:-4]
                try:
                    mlibfile = open("{}.mlb".format(x), "r")
                except IOError:
                    print("{}.mlb not found".format(x))
                    exit(-1)
                res = takemdefs(ctx, mlibfile, x)
                if isinstance(res, AssemblerError):
                    res.dump()
                    exit(-1)
                mlibfile.close()

        result = asm(ctx)
        if isinstance(result, AssemblerError):
            result.dump()
            exit(-1)

        with open("{}.obj".format(ctx.filename), "w") as f:
            genoc(ctx, result, f)

        if args.lstx:
            ctx.lst_me = True
        if args.lst or args.lstx:
            pretty_print(ctx, result, ctx.text)
        quit()


if __name__ == "__main__":
    main()
