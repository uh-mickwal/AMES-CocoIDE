# Macros  

macro ldadr/2
      ldi $1, $2
      ld $1, $1
mend

asect 0
start:
      ldadr r0, x

x: dc 34
halt
end
