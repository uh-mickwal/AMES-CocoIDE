# Timer IO test program
# Set Timer adr = 0xF0, vector = 2
asect 0
ei

start:
	ldi r1, 5
	ldi r0, 0xf0
	st r0, r1
start2:
	wait
	
	st r0, r1

waitint:
	ld r0, r1
	dec r1
	tst r1 # This is abuse!!!
	bnz waitint
	ldi r1, 0
	st r0, r1 # cancel timer
br start: # change to start2 to stop

thdlr: 
	ldi r2, 45
	ldi r2, 34
	ldi r1, 8
	st r0, r1
	rti
di 
halt
asect 0xf4	# interrupt vector R=2
int0: dc thdlr, 0 #$bin
end
