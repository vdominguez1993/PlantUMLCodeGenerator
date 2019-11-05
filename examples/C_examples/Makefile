
.PHONY: generate clean build run

generate: example.c example.h

example.c example.h: UML_example.uml
	python3 ../../CodeGenerator.py -i UML_example.uml -o example.c,example.h -t ../../templates/C_code.c,../../templates/C_code.h

build: generate
	gcc -o example main.c example.c

run: example
	./example

clean:
	rm -f example.c example.h
