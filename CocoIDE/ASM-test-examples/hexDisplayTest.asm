#! Hex Display test program
#$arch=vn
asect 0
do	
	ldi r0,  0xF0 # IO port address in memory 
	
	#do
		ld r0, r1 # get keypress
		ldi r2, 0b10000000
		#and r1, r2
	#until nz
	ldi r2, 0b01111111
	#and r2, r1
	st r0, r1
	clr r2 # Set to zero 
until nz # Forever!
_halt>
halt


end 
