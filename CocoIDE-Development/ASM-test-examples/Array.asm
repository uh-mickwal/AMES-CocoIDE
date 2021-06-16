# A program that counts how many items in an array of integers
# with starting address intArray are less than or equal to an 
# integer placed in a memory cell labelled y. The total number
# of items in the array (its length) should be placed in the 
# memory cell labelled n, and the resulting count should be 
# stored to the cell labelled result
# Suggested algorithm:
#count = 0
#index = 0
#while index < mem[n]
#	current = mem [intArray+index]
#	if current <= mem[y]
#		count = count + 1
#	index = index + 1
# mem[result] = count

asect 0
ldi r0, intArray # r0 = start address of array


ldi r1, n		 # r1 = mem[n] = size of array
ld r1, r1	# r1 = mem[y]

clr r2 # r2 = mem[index]	
clr r3 # Count = 0

# iterate htrough the array
while
tst r1
stays nz 	# while count > zero
	
	ld r0, r2 	# gets next item into r2
	push r1 # save r0 to stack, frees up r1
		# Load r1 withthe compare value
		ldi r1, y
		ld r1, r1
	
		if 
		cmp r2, r1 # if mem[r0] <= mem[y]
		is le
			inc r3
		fi
	
	pop r1
	inc r0
	dec r1 # r1 = r1 -1
wend


ldi r0, result
st r0, r3	# Store count in mem[result] 


halt
#data
intArray: dc 20, 23, 45, 2, 1, 7, 8, 3, 4, 5
n: dc 10
y: dc 11
result: ds 1
end 


