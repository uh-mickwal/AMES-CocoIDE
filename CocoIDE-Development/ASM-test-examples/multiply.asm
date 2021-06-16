asect 0

ldi r0, x
ld r0, r0
ldi r1, y
ld r1, r1
clr r2

# Signed mumber adjust. 
if 	
tst r0
is mi		#If y is -ve,negate x and y
	neg r1
	neg r0
fi

# Multiply by repeated addition
while	
# Note, Z flag already set by neg tst r0, neg r0 above, 
# or by dec r0 below.
stays nz
	add r1, r2
	dec r0 # count down towards zero
wend

# Save result 	
ldi r0, res
st r0, r2
halt
x: dc -2	#$dec
y: dc -10		#$dec
res: ds 1	#$dec
end