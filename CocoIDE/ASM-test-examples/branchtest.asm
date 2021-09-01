asect 0
	ldi r0, 1
	dec r0
	#bz test1
	dec r0
	bmi test2
	
 	
asect 0x20
test1:
		ldi r1, 3
		halt
		
asect 0x30
test2:	ldi r1, 4
		halt
end
	
	