asect 0

ldi r0, endA-A
push r0		# second parameter, length
ldi r0, A
push r0		# first parameter, marks
jsr median
addsp 2
ldi r3, medA
st r3,r0		# medA= median(marks, length)

ldi r0, endB-B
push r0		# second parameter, length
ldi r0, B
push r0		# first parameter, marks
jsr median
addsp 2
ldi r3, medB
st r3,r0		# medA= median(marks, length)


halt

A: dc 9,0,5,3,2,1,7,3,2,10,5,11,1,10,4,3,0,9,4
endA:
B: dc 1,1,1,2,4
endB:

medA: ds 1
medB: ds 1

median:			# subroutine median(marks, length) result in r0
push r1
push r2
push r3			# save registers

addsp -12		# allocate array histogram

# initialise histgram with zeroes
ldsa r1, local.histogram		# r1 -> histogram
ldi r2,12	# r2 is a down counter
clr r0
while
  dec r2
stays pl
  st r1,r0
  inc r1
wend

# scan 'marks' and accumulate histogram
# use r2 as work register
clr r1				# r1 is index
while
  ldsa r2, local.length
  ld r2,r2
  cmp r1, r2	# index<length
stays lt
  
  ldsa r0, local.marks
  ld r0,r0	# r0 -> marks[0]
  add r1,r0 # r0->marks[index]
  ld r0,r0  # r0= m = marks[index]

  ldsa r3, local.histogram
  add r0,r3 # r3-> histogram[m]

  ld r3, r2
  inc r2
  st r3, r2	# histogram[m] = histogram[m] + 1

  inc r1		# index = index +1
 
wend

clr r0	# med
clr r1  # acc

ldsa r3, local.length
ld r3,r3		# r3=length
inc r3			# r3=length+1
shra r3			# r3=(length+1)//2

while
   cmp r1,r3
stays lo
   ldsa r2,local.histogram
   add r0,r2
   ld r2,r2		# r2=histogram[med]
	
	add r2, r1	# acc = acc + histogram[med]
	inc r0			# med = med +1	
wend

dec r0

addsp 12			# deallocate histogram

pop r3				# restore registers
pop r2
pop r1
rts					# return

tplate local
histogram:  ds 12
			ds 3		# saved registers
			ds 1		# return address
marks:		ds 1
length:		ds 1

end