# CDM8 Assembly language syntax/highlighter definitions
# M L Walters, V1 Sept 2016
# CocoIDE V 0.93
# CocoIDE V1.0+  Update for CDM8 V4 Assembly Language Version + additional standard macro defs
# CocoIDE V1.1   CDM8 V5: rol replaced by swan. Changed rol to macro for backwards compatability,  

language = "CDM8 Assembly Language"
fileext = ".asm"
version = "V1.1"
screenScaleMode = False # = "Presenter mode" scales main window to fill
                        # screen, also good for smaller screens.
                        # False = "Lab PC mode" smaller fixed window size.
                        # Note, -p option overides this setting to scale display.


helpFile="CocoIDE-SoftwareManual.pdf"
basefont=None#"monospace 6" # None = system default font. Try "courier 10 bold", "monospace 12", "arial 11" etc.
watchtrigs = ["dc", "ds"]
labelspec = [":", ">"]
entrySpec = "_" # If label starts with this, add to RunFrom menu
labelcolour = "brown"
commentprefix = "#"
commentcolour="slate gray"
PCcolour = "orange"
SPcolour = "medium orchid"
membgColour = "white"
#memEmptyColour = "light grey"
memColour = "black"
chMemColour = "red"
bpColour = "grey"
errColour = "pink"
indent=4
iportColour = "royal blue"
oportColour = "green3"
ioportColour = "aquamarine4"#"cyan4"#"PaleTurquoise4"

highlights ={"blue":["r0", "r1", "r2", "r3",
                "ld", "st", "ldi", "ldc", "move",
                "add", "addc", "sub", "cmp", "and", "or", "xor", "not",
                "neg", "dec", "inc", "shr", "shra", "shla", "swan",
                "push", "pop",
                "jsr", "rts", "osi", "osix", "rti", "crc",
                "br", "beq", "bz", "bne", "bnz", "bhs", "bcs", "blo",
                "bcc", "bmi", "bpl", "bvs", "bvc", "bhi", "bls",
                "bge", "blt", "bgt", "ble", "ret", "noop", "wait", "halt",
                "pushall", "popall", "setsp", "addsp", "ldsa",
                "ioi", "rti", ],#"osix"], # osix removed, only needed for paged mem

        "green":["asect", "rsect", "end", "dc", "ds", "ext", "tplate", "set",
                    "page"],

        "purple":[  "run", "else", "if", "fi", "is",
                    "gt", "lt", "le", "ge", "mi", "pl", "eq", "ne", "z", "nz",
                    "cs", "cc", "vs", "vc","hi", "lo", "hs", "ls",
                    "macro", "mpop", "mpush", "mend",
                    "continue", "wend", "until", "while",
                    "save", "restore", "define", "stsp", "ldsp",
                    "stays", "true", "break", "tst", "clr", "do",
                    "then", "unique", "first_item", "item", "last_item",
                    "jmp", "jsrr", "shl", "banything", "bngt", "bnge", "bneq",
                    "bnne", "bnlt", "bnle", "bnhi", "bnhs", "bncs", "bnlo",
                    "bnls", "bncc", "bnmi", "bnpl", "bnfalse", "bntrue",
                    "bnvs", "bnvc", "bnvs", "define", "ldv", "stv",
                    "ei", "di", "rol", "nop" ]
        }


# Not implemented
delim = ","
hexprefix = "0x"
binprefix = "0b"
numcolour = "black"
srtdelim = '"'
alphachrs = "abcdefghijklmnopqrstuvwABCDEFGHIJKLMNOPQRSTUVW_"
numchrs = "01234567890abcdefABCDEF-+"
bracketleft = ["[", "{", "("] #Not used - too slow
bracketright = ["]", "}", ")"]# Not used - to slow




