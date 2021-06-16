# Array program

asect 0

ldi r0, array # Address pointer for mem[r0]

#ldi r1, n
#ld r1, r1	# index into array item
clr r1

clr r2 		# array item i.e mem[r0]
clr r3 		# Result or total etc.


while
ldi r2, n
ld r2, r2 # r2 = n
cmp r1, r2
stays  ne
	ld r0, r2
	# save r0, and r1
	push r0
	push r1
		# do processing here, free r0 and r1
	
	
	# restore r0 and r1
	pop r1
	pop r0
	inc r0
	inc r1
wend 


ldi r0, res
st r0, r3




halt

# Data section
array: dc 1, 3 , 4, 6, 8, 10, 20, 22, 30, 4
n: dc 10
res: ds 1

end 