asect 0
ldi r0, 0xf0

while
	ld r0, r2
	tst r2
	stays z
wend

halt




end
