This folder will contain the latest stable version of CocoIDE, example assembly program (helloprog.asm) and the CocoIDE manual (slightly outdated!). 


Installation:  
Make sure that you have Python installed (V3+ prefered, but should work ok with Python 2.7). Visit www.python.org and follow the installation instructions for your OS (Linux, MAC/OSX OR Windows). When installing Python, make sure the install py.exe (Python) launcher option is enabled. Also to run CocoIDE from a terminal or command line interface, select the "Modify Environment Variables" option.


Then download the CocoIDE.pyzw program file (click on CocoIDE.pyzw file and select Download from the Github side menu) and save to a folder on your local hard drive. From your File Manager/Explorer simply Double click to run. 


Troubleshooting:  
You may have to configure your File Manager, File Explorer, Finder program etc. to open the CocoIDE.pyzw with "python" or "pythonw". Right click and select "Open with" and choose python or pythonw, and make this the default action for this file type.

MAC/OSX: In later versions of OSX, folders that are linked to external (i)cloud services have security permissions set that do not allow Python programs to run. To avoid this, make sure you save the CocoIDE.pyzw download to a new folder created directly under your home directory or folder, making sure that it is not linked to any cloud services. 

If the CocoIDE.pyzw file still does not run correctly, you may find that using the uncompressed source code version will run ok. Simply download all the files from the CocoIDE-Download/Source/ folder and extract the files to a new local folder. If double clicking the cocoide.pyw source file does not work, open the cocoide.pyw file in IDLE (the Python IDE) and Select Run from the Run menu.


Testing:  
The test assembly program "helloProg.asm" demostrates a number of features of programming the CDM8 processor with CocoIDE. To see the OP message click on IO +, and add an OP_Disp_16xChr (16 Character memory mapped display device) at memory location 0xEO. Click "Compile/Reset" then "Start".

