asect 0

ldi r0, x
ld r0, r0	# r0 = mem[x]
ldi r1, y
ld r1, r1	# r1 = mem[y]
clr r2

# Signed mumber adjust. 
if 	
tst r0
is mi		#If x is -ve,negate x and y
	neg r1
	neg r0
fi

# Multiply by repeated addition
while	
# Note, Z flag already set by neg tst r0, neg r0 above, 
# or by dec r0 below.
stays nz
	if
	add r1, r2
	is vs	# Signed overflow detect
		ldi r0, error
		ldi r1, 1
		st r0, r1
		break
	fi
	dec r0 # count down towards zero
wend

# Save result 	
ldi r0, res
st r0, r2
halt
x: dc 2	#$dec
y: dc 10		#$dec
res: ds 1	#$dec
error: ds 1
end