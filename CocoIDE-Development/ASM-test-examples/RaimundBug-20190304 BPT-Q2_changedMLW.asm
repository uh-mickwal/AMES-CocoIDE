asect 0
#!#####################################
#! Array Programming.
#!
#! Write a program below that scans an array of 10 integers,
#! starting at location array.
#!
#! Your program should find all array elements are less than -4
#!   a) count these elements
#!   b) build the sum of these elements
#!   c) negate these elements and store back to array
#!
#! Store the result of a) and b) in the location labelled 'res'.
#!
#! For example, if the content of the array is:
#!    5,-5,11,-12,-8,0,-6,0,-2,3
#! then answer a) should be 5 (elements -5,-12,-8,-6)
#! then answer b) should be -31 (sum -5 + -12 + -8 + -6)
#! then answer c) should be array 5,3,11,12,2,0,6,0,1,3
# Step 1: iterate 10 times
clr r0	# r0: loop counter 'i'
while
  ldi r1,10
  cmp r0,r1
stays lt	# (i<10)
  #========================================
  # Step 2: Load array element
  ldi r2,array	# r2 --> array[0]
  add r0,r2		# r2 --> array[i]
  ld r2,r2		# r2 = array[i]
  # Step 3: Compare array element
  if
    ldi r3,-4
    cmp r2,r3
  is lt		# (array[i]<-4)?
    # Step 4: action: negate
    neg r2	# r2 = -array[i]
    # Step 5: store element back
    ldi r3,array	# r3 --> array[0]
    add r0,r3		# r3 --> array[i]
    st r3,r2		# array[i] = -array[i]
  fi
  #========================================
  inc r0	# i++
wend
#========================================
ldi r0,array	#! use array for question c)
tst r0
tst r0
halt		#!
asect 0x90
#! ######### INITIAL DATA, you MAY change ONLY data values
DATA>		#!
array:	dc  5,-3,11,-12,-2,0,-6,0,1,3 # change values after 'dc'
ENDDATA>	#!
res:	ds 1	#!
end
