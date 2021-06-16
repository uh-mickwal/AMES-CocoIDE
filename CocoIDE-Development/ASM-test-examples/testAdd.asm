# M L Walters, 5 July 2015
# Test Program: res = a + b
asect	0


start:		# your solution starts here
	# replace ... with the your code, continue on lines below.
	ldi	r0, a
	ld 	r0, r1	# Load r1 with a
	ldi 	r0, b
	ld 	r0, r2	# Load r0 with b
	add	r1, r2	# (a + b -> r1
	ldi	r0, res
	st	r0, r2	# Put result in memory

      # at this point 'res' has the answer
finish:
      halt

asect 0x20
Data:
a:	dc	0x07 	# replace 0 by your choice of a for testing
b:	dc	0x07 	# replace 0 by your choice of b for testing
asect 0x30
res:	ds	1
end
