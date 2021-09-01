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

asect 0
ldi r0, a
ld r0, r0 # r0 = mem[a]

ldi r1, b
ld r1, r1 # r1 = mem[b]

clr r2 # r2 = count 
clr r3 # r3 = total

if
tst r0
is mi
	neg r0
	neg r1
	if 
	tst r1
	is mi
		neg r1
	fi
fi

while
cmp r2, r0
stays lt # signed representation for less then condition
	if
	add r1, r3
	is vs
		ldi r0, error
		ldi r1, 1
		st r0, r1
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
a: dc -2
b: dc -3
result: ds 1
error: ds 1
end
