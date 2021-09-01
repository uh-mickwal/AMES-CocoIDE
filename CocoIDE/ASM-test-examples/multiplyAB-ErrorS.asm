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

# Re-write the above so that the program exits the loop early 
# when the total is higher than 255 (i.e. there is an unsigned
# number overflow), and indicates that this has happened by 
# storing 1 to a memory cell labelled error (otherwise this 
# memory cell should end up containing 0)

asect 0 
ldi r0, a
ld r0, r0	# r0 = mem[a]

ldi r1, b
ld r1, r1	# r1 = mem[b]

clr r2 	# r2 = count
clr r3	# r3 = total

# Signed number sign adjustment to get correct sigh of result
if 
tst r0
is mi
	neg r0
	if
	tst r1
	is mi
		neg r1
	fi
fi

# do the multipolication by repeated additon
while
cmp r2, r0
stays lt # Using signed numbers
	if
	add r1, r3 # total(=r3) = total + mem[a](=r1)
	is vs
		break
	fi
	inc r2
wend

# Check for unsigned overflow
if 
is vs	# if C still set (i.e unsigned overflow has occurred
	ldi r0, 1
	ldi r1, error
	st r1, r0
fi #else
	# Store the Result in r3, at this point
	ldi r0, result
	st r0, r3
#fi

halt 
# Program data
a: dc -10
b: dc 0
result: ds 1
error: ds 1
end