


asect 0x00
  ldi r0, a
  ld  r0, r0
  ldi r1, b
  ld  r1, r1
  add r0, r1
  ldi r0, result
  st  r0, r1
  halt
a: dc 0xAE
: dc 0x03
result:
   ds 1
end


asect 0x00
  ldi r0, a
  ld  r0, r0
  ldi r1, b
  ld  r1, r1
  add r0, r1
  ldi r0, result
  st  r0, r1
  halt
a: dc 0xAE
: 0x03
result:
   ds 1
end


asect 0x00
  ldi r0, a
  ld  r0, r0
  ldi r1, b
  ld  r1, r1
  add r0, r1
  ldi r0, result
  st  r0, r1
  halt
a: dc 0xAE
b: dc
result:
   ds 1
end

