	asect 0
	
	setsp 0xf0		# set the stack below I/O segment

	ldi r0, begin	# simulate interrupt for setting Interrupt Emabled in PS
	push r0			# push new PC, address 'begin'
	ldi r0,0x80		# 0x80 means "interrupt enabled"
	push r0			# push new PS
	rti				# return from interrupt to address 'begin'
	
begin:
	ldi r0,0xf3		# 0xf3 is IO-3, our keyboard/display device
	clr	r1			# clear the current value (we keep it in r1)
	wait			# wait for an interrupt
	
start:				# if we are here, the first interrupt has happened
	add	r3,r1		# add current increment to r1
	st	r0,r1		# and display it on the hex display
	br start		# close the loop
	
	

# INTERRUPT SERVICE ROUTINE
ISR: 
	push r0
	push r1
	push r2			# we are going to use these regs
	
	ldi r0,0xf3
	ld	r0,r1		# read the key code
	
	ldi r2,0x61	#
	cmp	r2,r1		#
	bne	notA		# is it 'a' (ASCII 0x61)? 
	ldi	r3,1		# yes, current increment is now 1
	br	exit

notA:	
	ldi	r2,0x62	# 
	cmp	r1,r2		#
	bne	exit		# is it 'b' (ASCII 0x62)? if not, exit
	ldi	r3,-1		# yes, it is 'B'. Set increment to -1
	

exit:				# restore registers and rerturn from interrupt
	pop r2
	pop r1
	pop r0
	rti


# interrupt vector R=2
	asect	0xf4	# 0xf0+2*R
int2: dc	ISR,0 	# PC & PS, PS shows interrupts disabled

	end
	
