macro get/2 # Gets a value from memory addr ($1) to rn ($2)
      ldi $2, $1
      ld $2, $2
mend

macro put/2 # Puts reg ($1) contents to memory addr ($2)
	unique $1, temp
	push ?temp
	ldi ?temp, $2
	st ?temp, $1
	pop ?temp
mend


asect 0

get u, r0 #
get v, r1
get w, r2
ldi r3, 4
#ld r0, r0
#ldi r1, v
#ld r1, r1
#ldi r2, w
#ld r2, r2
if
	cmp r0, r3
	is z, or#, and	#and	###### Error here!! Ok with and?
	add r3, r3
	is nz
then
	add r2,r2
else
	ldi r3, 2
fi

while
	tst r0
stays nz
	inc r0
until z





halt

DATA1>            #!
u:  dc 3               #  only change values after 'dc'
v:  dc 4               #  only change values after 'dc'
w:  dc 5               #  only change values after 'dc'
ENDDATA1>   #!

result:     #!
G:    ds  1   #!
end
