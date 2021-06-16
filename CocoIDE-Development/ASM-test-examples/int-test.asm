asect 0
	ldi r0, start
	push r0
	ldi r0, 0x80
	push r0
	rti
	halt

start:
	ldi r0, 34
	
	halt
end