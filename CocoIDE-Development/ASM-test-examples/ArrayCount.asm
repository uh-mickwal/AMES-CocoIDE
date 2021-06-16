# A program that counts how many items in an array of integers 
# with starting address intArray are less than or equal to an 
# integer placed in a memory cell labelled y. The total number of
# items in the array (its length) should be placed in the memory
# cell labelled n, and the resulting count should be stored to
# the cell labelled result
# Suggested algorithm:
# count = 0
# index = 0
# while index < mem[n]
# 	current = mem [intArray+index]
#	if current <= mem[y]
#		count = count + 1
# index = index + 1
# mem[result] = count

asect 0

ldi r0, intArray # Array start address

ldi r1, n		
ld r1, r1 		# Size of array in r1

ldi r2, y
ld r2, r2		# r2 = y = compare numer


clr r3 			# count total

while
tst r1
stays nz  # while count > 0
	push r1
		ld r0, r1
		if 
		cmp r1, r2
		is lt
			inc r3
		fi
	pop r1
	dec r1
	inc r0
wend
# Result now in r3
ldi r0, result
st r0, r3


halt
# data section
intArray: dc 1, 2, 5, 6, 7, 4, 20, 23, 11, 25
n: dc 10
y: dc 9
result: ds 1
end