# Not workimng yet!


macro bit0/1
	unique $1, mask
	push ?mask
	ldi ?mask, 0b00000001
	and $1, ?mask
	pop ?mask
mend


asect 0
ldi r1, 11
ldi r2, 12
ldi r3, 13

ldi r0, 0b10001001

bit0 r0


halt
end
