# Keyboard test program
asect 0
ei
ldi r0, keyb
ldi r1, "q"
ldi r3, 0b01111111
do 
	ldi r3, 0b10000000
	ld r0, r2
	and r2, r3
	ldi r3, 0b01111111
	and r3, r2
until z

halt

int0: 
	ldi r1, "*"
	rti
	
int1:
	ldi r1, "%"
	ldi r1, "%"
	ldi r1, "%"
	ldi r1, "%"
	ldi r1, "%"
	ldi r1, "%"
	rti

asect 0xE0
keyb: ds 1
asect 0xF0
ints: dc int0, 0b00000000, int1, 0b00000000 #$hex

end
