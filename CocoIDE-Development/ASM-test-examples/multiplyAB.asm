# A program that employs repeated addition to perform 
# multiplication of two unsigned numbers placed in memory cells
# at locations labelled a and b, and stoores the product of these
# two numbers in a memory cell labelled result, such that
# 	mem[result] = mem[a] * mem[b]
# Suggested algorithm:
#
# count = 0
# total = 0
# while count < mem[a]
#	total = total + mem[b]
#	count = count + 1
# mem[result] = total

asect 0 
ldi r0, a
ld r0, r0	# r0 = mem[a]

ldi r1, b
ld r1, r1	# r1 = mem[b]

clr r2 	# r2 = count
clr r3	# r3 = total


# do the multiplication by repeated additon
while
cmp r2, r0
stays lo # Using unsigned numbers
	add r1, r3 # total(=r3) = total + mem[a](=r1)
	inc r2
wend
# Result in r3, at this point
ldi r0, result
st r0, r3

halt 
# Program data
asect 0xE0
a: dc 102
b: dc 3
result: ds 1
end