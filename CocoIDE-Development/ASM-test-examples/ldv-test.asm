asect 0
	ldv y, r0
	stv r0, y 
	halt
	
	
asect 0x20
x:	dc 0x34
y:	ds 1 #$hex

end