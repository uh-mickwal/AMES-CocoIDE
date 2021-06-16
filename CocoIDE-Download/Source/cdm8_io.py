#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python3 and 2
from __future__ import absolute_import, division, print_function

# CdM8 IDE and emulator
# (c) M L Walters and A Shafarenko June-July 2018
# 

# July 2018, M L Walters
# V1.6 Seperate out IO Ports into (this!) seperate module:
# V1.7 Added IO ports 
# V1.8 Commented out Memory Manager (CocoIDE V1.97 removed paged memory menu item)
# To do:    terminal, gRobotIF, LogisimIF, graphics??, DMA? 
ver = "V1.8"

try:
    # Python 3 tk
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    from tkinter import messagebox
    import tkinter.font as font
except:
    # Python 2 tk (runs but not exhaustively tested!)
    # Ames lib (sendfile.py) not python 2 compatible (urllib)
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    import tkFont as font
from sys import platform


import cdm8_asm as cf # Configuration and defaults file

# Global vars
interruptVectors = []
IDE = None
memDict = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7}

class IOport():
    """
    To create an IO port, inherit from IOport. Parameters parent, portno, portAdr
    and name to IOport.--init__()
    the New class should create the main display on self.IOdispwin
    The name of the new IO port (class) is the name shown in the IO port drop list
    New class shouls contain two mthods:
     __init__() # called when instantiating new port
     updatePort() # updates the port display. 
     Note:
            self.portIPvals = {} # dictionary of input port {adresss:value} pairs
            self.portOPvals = {} # dictionary of output port {address:value) pairs
        These are automatically updated and read by CocoIDE, your updatePort() method
        should just update the Port Display
            
    """
    # Should be shared between all child object ports
    ## Interrupts will be picked up at beginning of next self.emu.step(), via CocoIDE.runProg()
    global interruptVectors # Interrupt vector default = []. If not empty list, will raise interrupt
    
    def __init__(self, parent=None, portno=0, portAdr=0xf0, name="Untitled"):
        self.portno = portno
        self.parent = parent
        self.portAdr = portAdr+self.portno #default memory Address
        self.prevAdr=None
        self.name = name
        self.prevRetVec = 0
        self.retVectorVar = tk.StringVar()
        # Dictionaries to hold IP and OP values. Set to None in Super class if not used
        # Define more entries if more than one adr/port/IOs required etc.
        self.portIPvals = {} # default input port adresss:values
        self.portOPvals = {} # default output port addresses:values
        ## Create the Standard IO port container - Super Class needs only fill self.IOdispwin
        #  with GUI widgets etc.
        self.portFrame = tk.Frame(self.parent, width=358)
        #self.portFrame.grid(row=self.portno, sticky="ew")
        self.portFrame.pack(fill=tk.X, expand=1)
        #self.portFrame.columnconfigure(0, weight=1)
        
        # Title/header/standard widgets frame
        self.portheaderFrame = tk.Frame(self.portFrame, relief="raised", border=1)
        self.portheaderFrame.pack(side=tk.TOP, fill=tk.X, expand=1)
        
        # Port Address Entry Box 
        self.adrBoxtxt = tk.StringVar()
        self.adrBoxtxt.set("%02X" % self.portAdr)
        self.IOadrBox = tk.Entry(self.portheaderFrame, width=2, text=self.adrBoxtxt)
        self.IOadrBox.pack(side=tk.LEFT, fill=tk.X)
        self.IOadrBox.bind('<Return>', self.updatePortAdr)
        
         
        ## Delete port button?
        # Make the button smaller to look like a close button
        # size in pixels
        f = tk.Frame(self.portheaderFrame, height=15, width=15)
        f.pack_propagate(0) # Do not shrink
        f.pack(side=tk.RIGHT)
        self.portcheck = tk.IntVar()
        self.portcheck.set(0)
        self.delButton = tk.Button(f, text="X", command=self.removePort )# variable=self.portcheck)
        self.delButton.pack(fill=tk.BOTH, expand=1)# 
        
        # Make header look nice!
        self.spacer = tk.Label(self.portheaderFrame, width=12)
        self.spacer.pack(side=tk.LEFT, expand=0)
        
        # Configure a larger font for displays
        self.dispfont = font.nametofont("TkDefaultFont").copy()  # Get its font
        self.dispfont.config(size=int(self.dispfont["size"]*1.3), weight="bold")   # Modify font attributes
        
        # Port type/title
        self.title = tk.Label(self.portheaderFrame, text=self.name.ljust(30))
        self.title.pack(side=tk.LEFT, fill=tk.X, expand=1)
        
        # IO port GUI area/panel
        self.IOdispwin = tk.Frame(self.portFrame, height=15, relief="sunken")#,bg="green")
        self.IOdispwin.pack(side=tk.TOP, fill=tk.X, expand=1)
        #self.portno += 1
    
    def getIPadr(self):
        return list(self.portIPvals.keys())
        
    def getOPadr(self):
        return list(self.portOPvals.keys())
    
    def getIPval(self):
        return self.portIPvals.values()
    
    def setOPval(self, adr=None, val=0):
        if adr == None: adr = self.portAdr
        #print ("%%", adr)#debug
        if  adr in self.portOPvals.keys():
            #print("**", adr, val)#debug(
            self.portOPvals[adr]= val
            self.updatePort()
            
    def resetPort(self, event=None):
        for item in self.portOPvals.keys():
            self.portOPvals[item] = 0
        self.updatePort() 

    def updatePortAdr(self, event=None):
        #Check value returned
        error = None
        numstr = self.adrBoxtxt.get().upper()
        if len(numstr) == 2:
            for char in numstr:
                if char not in "0123456789ABCDEF":
                    error = True
        else: 
            error = True
        # if ok, update port address
        if not error:
            self.adrBoxtxt.set(numstr)
            numIPadrs = len(self.portIPvals)
            numOPadrs = len(self.portOPvals)
            self.portIPvals = {}#: del self.portIPvals[self.portAdr]
            self.portOPvals = {}#: del self.portOPvals[self.portAdr]
            self.portAdr = int(numstr, 16)
            for n in range(numIPadrs):
                #print("n=",n, self.portAdr+n)
                self.portIPvals[(self.portAdr+n)] = 0x00
            startAdr = self.portAdr
            for n in range(numOPadrs):
                #print("n=",n, self.portAdr+n)
                self.portOPvals[(self.portAdr+n)] = 0x00
            #print(self.portIPvals)# debug
            #print(self.portOPvals)# debug
        else:
            self.adrBoxtxt.set("%02X" % self.portAdr)
        self.updatePort()
    
    def _updatePort(self):
        self.parent.event_generate("<<updatePort>>", state=256)
        
    def removePort(self, event=None):
        self.portFrame.destroy() # Remove itself!
        # Generate event in Super class to clear up IOports list etc.
        self.parent.event_generate("<<updatePort>>", state=str(self.portno))
    
    def updateFont(self):
        newsize = font.nametofont("TkDefaultFont")["size"]  # Get master/parent font size
        self.dispfont.config(size=int(newsize *1.3), weight="bold") # update
        
    def setInterrupt(self, vector=0):
        global interruptVectors # Interrupt vector 
        # Generates a hardware interrupt for the CDM8 machine.
        # Will be serviced, after the current instruction has been completed
        # then reset.
        interruptVectors += [vector]
        #print("£", vector, interruptVectors)
     
    
        

### IO Ports (inherit from IOport)

class OP_LEDs_8x1(IOport):
    
    def __init__(self, parent=None, portno=0, portAdr=0xf0):
        self.name=self.__class__.__name__ # IO port name for title
        IOport.__init__(self, parent, portno, portAdr, self.name)
        self.portOPvals = {self.portAdr: 0x00}# Only outputs needed
        self.portIPvals={}
        # Create the port GUI
        self.opLabels=[]
        for n in range(8):
            self.opLabels.append(tk.Label(self.IOdispwin, text=str(n), width=2, 
                fg="white", bg="green", relief="sunken", border=3, padx=7))
            self.opLabels[-1].pack(side=tk.RIGHT, expand=1)
        #self.updatePort()
    
    def updatePort(self, event=None):
        # Check if address needs updating
        if self.portAdr != self.prevAdr:
            self.portOPvals = {self.portAdr:0x00}
            self.portIPvals = {}
            self.prevAdr=self.portAdr
            
        # Then update the port IO registers    
        newval= self.portOPvals[self.portAdr]
        for n in range(len(self.opLabels)):
            mask=0b00000001
            for bit in range(8):
                if newval & mask:
                    self.opLabels[bit].config(bg="yellow", fg="black")
                else:
                    self.opLabels[bit].config(bg=cf.oportColour, fg="white")
                mask = mask << 1
        IOport._updatePort(self) # Call back to update CocoIDE

class IP_Keybd_7Bit(IOport):
    def __init__(self, parent=None, portno=0, portAdr=0xf0):
        self.name=self.__class__.__name__
        IOport.__init__(self, parent, portno, portAdr, self.name)
        self.portOPvals = {}
        self.portIPvals = {self.portAdr:0} # Only Input port needed
        
        # Create the port display
        # Vars
        self.keybBuffer = [] # Character buffer
        self.prevIntvec = 0
        self.retVectorVar = tk.IntVar()
        self.retVectorVar.set("0")
        self.prevRetVec = "0"
        self.ctrlcVectorVar = tk.IntVar()
        self.ctrlcVectorVar.set("1")
        self.prevCtrlVec = "1"
        self.bufVar = tk.StringVar()
        self.bufVar.set("")
        # widgets
        self.intLabel = tk.Label(self.IOdispwin, text="Interrupt: Return Ctrl+C")
        self.intLabel.grid(row=0, column=0, columnspan=3, sticky="sew")
        self.vecLabel = tk.Label(self.IOdispwin, text="  Vectors:")
        self.vecLabel.grid(row=1, column=0, sticky="w")
        
        self.retVectorEntry = tk.Entry(self.IOdispwin, textvariable=self.retVectorVar,
             width=1)
        self.retVectorEntry.grid(row=1, column=1, sticky="w")
        self.retVectorEntry.bind("<Return>", self.updateVec)
        
        self.ctrlVectorEntry = tk.Entry(self.IOdispwin, textvariable=self.ctrlcVectorVar,
             width=1)     
        self.ctrlVectorEntry.grid(row=1, column=2)#, sticky="w")
        self.ctrlVectorEntry.bind("<Return>", self.updateVec)
        
        tk.Label(self.IOdispwin, text="Buffer=16 Chrs, Empty=Bit7").grid(row=0, column=4)#, rowspan=2)
        tk.Label(self.IOdispwin, text="    ").grid(row=0, column=3, rowspan=2, sticky="w")
        #tk.Label(self.IOdispwin, text="").grid(row=1, column=3, rowspan=2)
        self.bufEntry = tk.Text(self.IOdispwin,  height=1,# text="",# validate="all", validatecommand=self.updatePort,
             width=17, font=self.dispfont, fg="white", bg="royal blue")
        self.bufEntry.bind("<Key>", self.updatePort)#
        #self.bufEntry.bind("<Return>", self.updatePort)
        self.bufEntry.grid(row=1, column=4)
        self.updatePort()
        
    def getIPval(self):# Overide the parent method
        ret = IOport.getIPval(self)
        if self.keybBuffer: 
            if self.keybBuffer[0] < 32:
                self.bufEntry.delete("1.0", "1.0 + 1c")
            self.bufEntry.delete("1.0", "1.0 + 1c")
            del self.keybBuffer[0]
        self.updatePort(self, keypress=False)
        return ret
        
    def updateVec(self, event=None):
        #print("update vector")
        intvec = str(self.retVectorVar.get())
        if intvec[0] in "0123":
            self.prevRetVec = intvec[0]
            self.retVectorVar.set(intvec[0])
        else:
            self.retVectorVar.set(str(self.prevRetVec))
        
        intvec = str(self.ctrlcVectorVar.get())
        if intvec[0] in "0123":
            self.prevCtrlVec = intvec[0]
            self.ctrlcVectorVar.set(intvec[0])
        else:
            self.ctrlcVectorVar.set(str(self.prevCtrlVec))
        return
        
    def updatePort(self, event=None, keypress=True):
        #print("keyb updatePort")
        # Check and update buffer and IP port value/char
        if event and keypress:
            if event.keysym == "Return":
                #print("Return Interrupt")
                self.setInterrupt(vector=int(self.retVectorVar.get()))
            elif event.char: 
                # A valid character key has been pressed, limit to 7 bits and 16 chars
                asc = ord(event.char)
                if asc == 3: # Ctrl C Interrupt
                    #print("^C Interrupt")
                    self.setInterrupt(vector=int(self.ctrlcVectorVar.get()))
                elif asc < 32 and len(self.keybBuffer)<16: # Control Char.
                    self.keybBuffer.append(asc)
                    self.bufEntry.insert(tk.END, "^"+chr(asc+96)) # Leading ^
                elif len(self.keybBuffer)<16:
                    self.keybBuffer.append(asc) 
                    self.bufEntry.insert(tk.END, event.char)
        # Update Input port value (with next char)
        #print(self.keybBuffer)#debug
        if self.keybBuffer: 
            self.portIPvals[self.portAdr] = self.keybBuffer[0]    
        else:
            self.portIPvals[self.portAdr] = 0b10000000
        #print(self.portIPvals[self.portAdr])#debug
        IOport._updatePort(self)# Call back to update CocoIDE
        return "break"    



class IO_Timer(IOport):
    
    def __init__(self, parent=None, portno=0, portAdr=0xf0):
        self.name=self.__class__.__name__
        IOport.__init__(self, parent, portno, portAdr, self.name)
        ## Variables
        self.portOPvals = {self.portAdr:0}#self.portAdr:0} # Write and 
        self.portIPvals = {self.portAdr:0} # Read timer values
        self.timerStrValue = tk.StringVar()
        self.timerStrValue.set(str("%03d" % 0))
        self.timerValue = 0
        #timerIncrement = 1000 # 1000 msecs = 1 sec
        self.timerIncVar = tk.IntVar()
        self.timerIncVar.set(100) # 0.1 Sec
        self.timerInc = 100
        self.prevTimerValue = 0
        self.vectorVar = tk.StringVar()
        self.vectorVar.set("0")
        self.prevVec = "0"
        self.callback = False
        self.decrid = None
        
        ## Create the port GUI
        #Interuppt Vector
        tk.Label(self.IOdispwin, text="Interrupt Vector:", width=18).grid(row=0, column=0, sticky="w")
        self.vectorEntry = tk.Entry(self.IOdispwin, textvariable=self.vectorVar, width=1)
        self.vectorEntry.grid(row=0, column=1, sticky="w", )
        self.vectorEntry.bind("<Return>", self.updateVec)
        # Timer Decrement
        tk.Label(self.IOdispwin, text="Timer Decrement:", width=18).grid(row=1, column=0, sticky="w")
        tk.Radiobutton(self.IOdispwin, text="0.1sec", variable=self.timerIncVar,
            value=100).grid(row=1, column=1, sticky="w")#, command=self.tscaleSelect
        tk.Radiobutton(self.IOdispwin, text="1.0sec", variable=self.timerIncVar,
            value=1000).grid(row=1, column=2, sticky="w")#, command=self.tscaleSelect
        
        # Timer readout
        self.timerDisp = tk.Entry(self.IOdispwin,width=3, textvariable=self.timerStrValue, 
            font=self.dispfont, border=3,relief="raised", bg=cf.ioportColour, fg="white")
        self.timerDisp.bind("<Return>", self.setOPval)
        self.timerDisp.grid(row=0, rowspan=2, column=4)
        self.updatePort()
    
    def updateVec(self, event=None):
        #print("update vector")
        intvec = str(self.vectorVar.get())
        if intvec[0] in "0123":
            self.prevVec = intvec[0]
            self.vectorVar.set(intvec[0])
        else:
            self.vectorVar.set(str(self.prevVec))
        return
        
    def decrTimer(self, event=None):
        self.timerInc = self.timerIncVar.get()
        self.updatePort()
        #print(self.timerInc, "%",self.timerValue)# debug
        if self.timerValue > 0:
            self.timerValue -= 1
            self.decrid = self.parent.after(self.timerInc, self.decrTimer)
            self.callback = True
        else: # self.timerValue <= 0
            # generate interrupt
            self.setInterrupt(vector=int(self.vectorVar.get()))
            self.timerValue = 0
            self.prevTimerValue = 0 
            self.callback = False
    
    def setOPval(self, adr=None, val=None):
        # Overide parent setOPval
        if val == None: # Direct entered timer value
            val = int(self.timerStrValue.get())
            if val < 0 or val > 255:
                #self.timerStrValue.set(str("%03d" % self.prevTimerValue))
                val = self.prevTimerValue
        if val > 0:# and self.prevTimerValue != val: # If new timer setting
            self.timerValue = val
            self.prevTimerValue = val
        if self.timerValue > 0 and self.callback == False: 
            # Only if timer not currenly running set callback
            self.decrTimer()
        if val == 0 and self.callback == True:
            # Cancel timer
            # print("cancel timer", val)
            self.parent.after_cancel(self.decrid)
            self.timerValue = 0
            self.callback = False
            self.updatePort()
        
    
    def updatePort(self, event=None):
        self.portIPvals = {self.portAdr:self.timerValue}
        self.portOPvals = {self.portAdr:0}
        self.timerStrValue.set(str("%03d" % self.timerValue))
        IOport._updatePort(self)# Call back to update CocoIDE
        return           
                    
class IP_Buttons_8x1(IOport):
    def __init__(self, parent=None, portno=0, portAdr=0xf0):
        self.name=self.__class__.__name__
        IOport.__init__(self, parent, portno, portAdr, self.name)
        self.portOPvals = {}
        self.portIPvals = {self.portAdr:0} # Only Input port needed
        # Create the port GUI
        self.ipButtons=[]
        self.buttonNum = None
        self.resetPortVar = tk.IntVar()
        self.resetPortVar.set(1)
        tk.Checkbutton(self.IOdispwin, text="Reset\non Read", 
                var=self.resetPortVar).pack(side=tk.LEFT)
        # Create Input Buttons
        for n in range(8):
            self.ipButtons.insert(0, tk.Button(self.IOdispwin, text=str(n), width=1,    
                foreground="white", background="royal blue", highlightcolor="dark blue",
                activebackground="royal blue", activeforeground="white",
                relief="raised",
                border=3, #padx=7,
                command=lambda x=(n) : self.updatePort(button=x)))
            self.ipButtons[0].pack(side=tk.RIGHT, expand=1)
            self.btn =None
            for btn in self.ipButtons:
                btn.bind("<Button-1>", self.toggleButton)#updatePort)
                btn.bind("<ButtonRelease-1>", None)#self.releaseAllButtons)
                
                btn.bind("<Key>", lambda e: "break") #disable keys!
                #btn.bind("<Enter>", lambda e: btn.focus_force()) 
                #btn.bind("<KeyRelease-Return>", self.updatePort)
        self.updatePort()
    
    def toggleButton(self, event=None, button=None):
        if event and not button:# Get numberof button released
            #debug, 4=mouse button-1 down, 5 mouse button-1 release
            #print("%",self.resetPortVar.get(), event.type)
            if int(event.type) == 4 or int(event.type) == 5:# or self.resetPortVar.get() == 0:# and event.type == 5): 
                n = 7 
                for btn in self.ipButtons:
                    if btn == event.widget: # find which button was released
                        button = n
                    n -= 1
        if button != None:
            #print("Button=", button, self.ipButtons[button].config("relief"))
            if "raised" in self.ipButtons[7-button].config("relief"):# == "raised":
                self.pushButton(button=button)
            else:
                self.releaseButton(button=button)
        return "break"
        
    def pushButton(self, event=None, button=None):
        if event and not button:# Get number of button pressed
            if int(event.type) == 4:# event = Mouse Button pressed 
                n = 7
                for btn in self.ipButtons:
                    if btn == event.widget: # find which button was pressed
                        button = n
                    n -= 1
                #print(self.ipButtons[n].state(), self.ipButtons[n+1].state())# debug
        if button != None:
            print("toggled down")
            self.ipButtons[7-button].config(relief="sunken")
            #print(self.portIPvals[self.portAdr], butt)
            portval = self.portIPvals[self.portAdr] | (1 << button) #+= 2**butt
            #print("portval", portval)
            self.portIPvals[self.portAdr] = portval
        IOport._updatePort(self)
        return "break"
    
    def releaseAllButtons(self, event=None):
        #print(self.resetPortVar.get())
        if self.resetPortVar.get() == 0:
            for btn in self.ipButtons:
            #    print(btn)
            #    btn.state(["!pressed", "!active"])
            #    #print(btn.state())
                btn.config(relief="raised")
            self.portIPvals[self.portAdr] = 0   
        IOport._updatePort(self)
        return "break"
        
    def releaseButton(self, event=None, button=None):
        if event and not button:# Get numberof button released
            #debug, 4=mouse button-1 down, 5 mouse button-1 release
            #print("%",self.resetPortVar.get(), event.type)
            if int(event.type) == 5:# event = Mouse Button released 
                n = 7
                for btn in self.ipButtons:
                    if btn == event.widget: # find which button was released
                        button = n
                    n -= 1
        if button != None:
            print("toggle up")
            print("Raised")
            self.ipButtons[7-button].config(relief="raised")
            #print(self.portIPvals[self.portAdr], butt)
            portval = self.portIPvals[self.portAdr] &  (~(1 << button)) #+= 2**butt
            #print("portval", portval)
            self.portIPvals[self.portAdr] = portval
        IOport._updatePort(self)
        return "break"
    
    def getIPval(self): #Override IOport getIPVal
        # Save current values
        val = self.portIPvals.values()
        # If reset on read is selected, reset port to 0
        if self.resetPortVar.get() == 1:
            self.portIPvals[self.portAdr] = 0
            # Reset buttons
            if self.resetPortVar.get() == 1:
                for btn in self.ipButtons:
                    btn.config(relief="raised")
        return val
        
    def updatePort(self, event=None, button=None ):
        # If port adr changed, update port address range
        # print(self.prevAdr, self.portAdr)debug
        if self.portAdr != self.prevAdr:
            self.portIPvals[self.portAdr] = 0x00
            self.prevAdr=self.portAdr
        IOport._updatePort(self)
        return "break"
"""
##?? In progress - not needed for non-paged memory
class OP_MemMgr(IOport):
    def __init__(self, parent=None, portno=0, portAdr=0xf0):
        self.name=self.__class__.__name__
        IOport.__init__(self, parent, portno, portAdr, self.name)
        ## Variables
        global memDict
        memDict = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7}
        self.portOPvals = {self.portAdr:0} # Write to port OP new val/map
        self.portIPvals = {}
        self.mmDict = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7}
        self.pageSelect = []
        self.pageSelectVars = []
        
        ## GUI
        tk.Label(self.IOdispwin, text="Map RAM Page: ").grid(row=0, column=0)
        tk.Label(self.IOdispwin, text="To RAM Page: ").grid(row=1, column=0, sticky="e")
        for n in range(8):
            tk.Label(self.IOdispwin, text="%01X" % n).grid(row=0, column=(n*2+1), sticky="w")
            if n < 7: # Add spaces
                tk.Label(self.IOdispwin, width=1).grid(row=0, column=(n*2+2))
            self.pageSelectVars.append(tk.IntVar())
            self.pageSelect.append( ttk.Combobox(self.IOdispwin, textvariable=self.pageSelectVars[-1],
            state='readonly', width=1, foreground="black", background="white"))
            self.pageSelect[-1].bind('<<ComboboxSelected>>',self.updatePort) # reset Program Counter
            self.pageSelect[-1]['values'] = [0,1,2,3,4,5,6,7]
            self.pageSelect[-1].current(n)
            self.pageSelect[-1].grid(row=1, column=(n*2+1), sticky="w")
        
    def removePort(self, event=None): #Overide IOpoort method
        # Reset memory mappings
        global memDict
        # restore default memDict
        memDict = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7}
        IDE.Emu.mm = memDict
        IOport.removePort(self) # then close the MM.
    
    def setOPval(self, adr=None, val=0):
        global memDict
        mappage = val & 0b0000111
        topage  = (val >> 4) & 0b00001111
        #print("Map page ", mappage, " to ", topage)
        if mappage > 7 or topage > 7:
            #print("")
            return "Run time Error!\nIllegal Memory Manager value\n Bits 3 and 7 should be 0"
        else:
            memDict[mappage] = topage
            #print(memDict)
            self.pageSelectVars[mappage].set(topage)
            IOport.setOPval(self,adr, val) # update IDE etc.   
        return
        
    def updatePort(self, event=None):
        global memDict
        if event:
            #print("Listbox chamged")
            memDict = {}
            n = 0
            for page in self.pageSelectVars:
                #n = page.curselection(0)
                #print("Page ", n," to ", page.get())
                memDict[n] = int(page.get())
                n += 1
        IDE.Emu.mm = memDict
        #print(" ",memDict,"\n", IDE.Emu.mm)
"""        
class OP_Disp_16xChr(IOport):
    def __init__(self, parent=None, portno=0, portAdr=0xe0):
        self.name=self.__class__.__name__
        portno=0 # Always zero for this
        IOport.__init__(self, parent, portno, portAdr, self.name)
        # Create the port GUI
        self.portOPvals={}
        self.prevAdr = None
        for n in range(16):
            self.portOPvals[self.portAdr+n] = 0x00   
        self.adrRangeLabel = tk.Label(self.IOdispwin, text=" to\n  %02X" % (self.portAdr+15))
        self.adrRangeLabel.grid()
        spacer = tk.Label(self.IOdispwin, text="", width=2)
        spacer.grid(row=0, column=1)
        
        self.charLabels=[]
        for n in range(16):
            self.charLabels.append(tk.Label(self.IOdispwin, text=" ", width=1,# padx=1,
                font=self.dispfont, pady=3, border=3,relief="raised", bg=cf.oportColour, fg="white"))
            self.charLabels[-1].grid(row=0, column=(n+2), sticky="ns")
        self.updatePort() 
    
    def updatePort(self, event=None):
        # If port adr changed, update address range
        #print(self.prevAdr, self.portAdr)
        if self.portAdr != self.prevAdr:
            self.portOPvals = {}
            self.prevAdr=self.portAdr
            self.adrRangeLabel.config(text="to\n"+"%02X" % (self.portAdr+15))
            #
            for n in range(16): 
                self.portOPvals[self.portAdr+n] = 0x00
            IOport._updatePort(self) # Call back to update CocoIDE
        
        #Update port display label chars
        n = 0
        for key, val in self.portOPvals.items():
            #print("*",key, val)
            if val != 0:
                self.charLabels[n].config(text=chr(val))
            else:
                self.charLabels[n].config(text="")
            n += 1
        return
        
class OP_HexDisps_xN(IOport):
    
    def __init__(self, parent=None, portno=0, portAdr=0xf0):
        self.name=self.__class__.__name__ # IO port name for title
        IOport.__init__(self, parent, portno, portAdr, self.name)
        self.portOPvals = {}# Only outputs needed
        self.noPorts = tk.StringVar()
        self.noPorts.set("3")
        self.charLabels = []
        self.spacer = []
        self.prevPorts = None
        # Display
        self.adrRangeLabel = tk.Label(self.IOdispwin, text="to %02X " % (self.portAdr+int(self.noPorts.get())-1))
        self.adrRangeLabel.grid(row=0, column=0, columnspan=2, sticky="w")
        self.noPortsLabel = tk.Label(self.IOdispwin, text="N=")
        self.noPortsLabel.grid(row=1, column=0, sticky="e")
        self.noPortsEntry = tk.Entry(self.IOdispwin, text=self.noPorts, width = 1)
        self.noPortsEntry.bind("<Return>", self.updatePort)#self.portNupdate)
        self.noPortsEntry.grid(row=1, column=1, sticky="e")
        tk.Label(self.IOdispwin, text=" ", width=1).grid(row=0, column=2, rowspan=2)
        self.charLabels=[]
        #self.portNupdate()
        self.updatePort()
        
    def updatePort(self, event=None):
        # Called by CocoIE if OP Port address is written to or changed

        # Check if num of OP ports or addreses have changed
        noports = int(self.noPorts.get()[0])
        self.noPorts.set(str(noports)) # Just use first character
        if str(noports) in "123456" and noports != self.prevPorts:
            #print("Redraw Hex disp")# debug
            # redraw the display
            for disp in self.charLabels:
                disp.destroy()
            self.charLabels=[]
            for disp in self.spacer:
                disp.destroy()
            self.spacer = []
            for n in range(noports): 
                self.charLabels.append(tk.Label(self.IOdispwin, text="", width=1, padx=1,
                    font=self.dispfont, pady=3, border=3,relief="raised", bg=cf.oportColour, fg="white"))
                self.charLabels[-1].grid(row=0, column=(n*3+5), rowspan=2, sticky="nsew")
                self.charLabels.append(tk.Label(self.IOdispwin, text="", width=1, padx=1,
                    font=self.dispfont, pady=3, border=3,relief="raised", bg=cf.oportColour, fg="white"))
                self.charLabels[-1].grid(row=0, column=(n*3+4), rowspan=2, sticky="nsew")
                self.spacer.append(tk.Label(self.IOdispwin, text="", width=0, padx=3))
                self.spacer[-1].grid(row=0, column=(n*3+6),rowspan=2, sticky="nsew")
        else: # Bad value. not in range 1 to 6, or alpha char
            self.noPorts.set(self.prevPorts)
        
        # Check if OP addresses need updating
        numports = int(self.noPorts.get())
        if self.portAdr != self.prevAdr or numports != self.prevPorts:
            #print("Updating Adrs")#debug
            self.portOPvals={}
            self.adrRangeLabel.config(text="to %X" % (self.portAdr+numports-1))
            for n in range(numports):
                self.portOPvals[self.portAdr+n] = 0x00
            self.prevAdr=self.portAdr
            self.prevPorts = numports
        
        # Then update the port display
        labIndex = 0
        for n in range(len(self.portOPvals)):    
            newval = int(self.portOPvals[self.portAdr+n])
            self.charLabels[labIndex].config(text="%X" % (newval & 0b00001111))
            labIndex += 1
            self.charLabels[labIndex].config(text="%X" % (newval >> 4))
            labIndex += 1
        IOport._updatePort(self) # Call back to update CocoIDE/Emu

class OP_DecDisps_2xN(IOport):
    
    def __init__(self, parent=None, portno=0, portAdr=0xf0):
        self.name=self.__class__.__name__ # IO port name for title
        IOport.__init__(self, parent, portno, portAdr, self.name)
        self.portOPvals = {}# Only outputs needed
        self.noPorts = tk.StringVar()
        self.noPorts.set("3")
        self.charLabels = []
        self.spacer = []
        self.prevPorts = None
        # Display
        self.adrRangeLabel = tk.Label(self.IOdispwin, text="to %02X " % (self.portAdr+int(self.noPorts.get())-1))
        self.adrRangeLabel.grid(row=0, column=0, columnspan=2, sticky="w")
        self.noPortsLabel = tk.Label(self.IOdispwin, text="N=")
        self.noPortsLabel.grid(row=1, column=0, sticky="e")
        self.noPortsEntry = tk.Entry(self.IOdispwin, text=self.noPorts, width = 1)
        self.noPortsEntry.bind("<Return>", self.updatePort)#self.portNupdate)
        self.noPortsEntry.grid(row=1, column=1, sticky="e")
        tk.Label(self.IOdispwin, text=" ", width=1).grid(row=0, column=2, rowspan=2)
        self.charLabels=[]
        #self.portNupdate()
        self.updatePort()
        
    def updatePort(self, event=None):
        # Called by CocoIE if OP Port address is written to or changed
        # Check if num of OP ports or addreses have changed
        noports = int(self.noPorts.get()[0])
        self.noPorts.set(str(noports)) # Just use first character
        if str(noports) in "123456" and noports != self.prevPorts:
            #print("Redraw Hex disp")# debug
            # redraw the display
            for disp in self.charLabels:
                disp.destroy()
            self.charLabels=[]
            for disp in self.spacer:
                disp.destroy()
            self.spacer = []
            for n in range(noports): 
                self.charLabels.append(tk.Label(self.IOdispwin, text="", width=1, padx=3,
                    font=self.dispfont, pady=3, border=3,relief="raised", bg=cf.oportColour, fg="white"))
                self.charLabels[-1].grid(row=0, column=(n*3+5), rowspan=2, sticky="nsew")
                self.charLabels.append(tk.Label(self.IOdispwin, text="", width=1, padx=3,
                    font=self.dispfont, pady=3, border=3,relief="raised", bg=cf.oportColour, fg="white"))
                self.charLabels[-1].grid(row=0, column=(n*3+4), rowspan=2, sticky="nsew")
                #self.spacer.append(tk.Label(self.IOdispwin, text="", width=1))
                #elf.spacer[-1].grid(row=0, column=(n*3+6),rowspan=2, sticky="nsew")
        else: # Bad value. not in range 1 to 6, or alpha char
            self.noPorts.set(self.prevPorts)
        
        # Check if OP addresses need updating
        numports = int(self.noPorts.get())
        if self.portAdr != self.prevAdr or numports != self.prevPorts:
            #print("Updating Adrs")#debug
            self.portOPvals={}
            self.adrRangeLabel.config(text="to %02X" % (self.portAdr+numports-1))
            for n in range(numports):
                self.portOPvals[self.portAdr+n] = 0x00
            self.prevAdr=self.portAdr
            self.prevPorts = numports

        # Then update the port display
        labIndex = 0
        for n in range(len(self.portOPvals)):    
            newval = int(self.portOPvals[self.portAdr+n])
            nibtxt = "0123456789.-+*/="[newval & 0b00001111]
            self.charLabels[labIndex].config(text=nibtxt)
            nibtxt = "0123456789.-+*/="[newval >> 4]
            labIndex += 1
            self.charLabels[labIndex].config(text=nibtxt)
            labIndex += 1
        IOport._updatePort(self) # Call back to update CocoIDE/Emu 
        
if __name__ == "__main__":
    # test
    myapp = tk.Tk()
    myapp.title("Test")
    IP_Buttons_8x1(myapp)
    #LEDs_8x1(myapp)
    #Disp_16xChr(myapp)
    #HexDisps_xN(myapp)
    #IP_Keybd_7Bit(myapp)
    #OP_MemMgr(myapp)
    #IO_Timer(myapp)
    myapp.mainloop()
