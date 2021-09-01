# Interrupt test program
#$page=0
#$arch=vn

asect 0
	addsp -32 # Make room for IO Device addresses
	# Interrupt enable
	#ldi r1, start
	#push r1
	#ldi r1, 0b10000000
	#push r1
	#rti
	ei	# Enable Inerrupts

start:	
	ldi r1, 1
	dec r1
	
	ioi 

	osix 0x01
	di	# Disable Interrupts
	halt


asect 0x30
	ldi r1, 2
	inc r2
	dec r2
	dec r2
	rti

asect 0xf0
	dc 0x30, 0b00000000
end

#$page=1
asect 0	