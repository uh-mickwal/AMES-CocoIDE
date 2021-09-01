# A program that employs repeated addition to perform 
# multiplication of two unsigned numbers placed in memory cells
# at locations labelled a and b, and stoores the product of 
# these two numbers in a memory cell labelled result, such that
#  	mem[result] = mem[a] * mem[b]
# Suggested algorithm:
# count = 0
# total = 0

# while count < mem[a]
#	total = total + mem[b]
#	count = count + 1
# mem[result] = total

# Re-write the above so that the program exits the loop early
# when the total is higher than 255 (i.e. there is an unsigned
# number overflow), and indicates that this has happened by 
# storing 1 to a memory cell labelled error (otherwise this
# memory cell should end up containing 0)
#
# mem[error] = 0
# count = 0
# total = 0
# while count < mem[a]
# 	total = total + mem[b]
# 	if total > 255
# 		mem[error] = 1
# 		break
#	count = count + 1
# mem[result] = total

asect 0
ldi r0, a
ld r0, r0 # r0 = mem[a]

ldi r1, b
ld r1, r1 # r1 = mem[b]

clr r2 # r2 = count 
clr r3 # r3 = total

while
cmp r2, r0
stays lo # unsigned representation for lower 
	if
	add r1, r3
	is cs
		ldi r3, 1
		ldi r0, error
		st r0, r1
		ldi r3, 0	# do not bother chaging result
		break
	fi
	inc r2
wend
# Result now in r3
# Store result to mem[result]
ldi r0, result
st r0, r3  # mem[result] = r3 = total

halt
# Data Section
a: dc 10
b: dc 30
result: ds 1
error: ds 1
end
