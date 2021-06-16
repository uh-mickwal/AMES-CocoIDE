asect 0
ldi r0,-1

ldi r1,-128

add r0,r1           # set V to 1

ldi r0,-14

ldi r1,-28

add r0,r1              # V should be set to 0, but remains 1 if it was set before

halt
end