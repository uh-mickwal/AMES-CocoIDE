# 13a + 3b
asect 0
	ldi r0, a
	ld r0, r1
	ldi r2, 13
	move r1, r3
	do
		add r1, r3
		dec r2
	until z
	ldi r0, b
	ld r0, r1
	ldi r2, 3
	do 
		add r1, r3
		dec r2
	until z
	# r3 contains result
	ldi r0, res
	st r0, r3
halt

a: dc 2
b: dc 3
res: ds 1


end