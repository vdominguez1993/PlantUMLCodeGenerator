
.PHONY: generate clean

generate: example.c example.h

example.c example.h: UML_example.uml
	python3 ../../CodeGenerator.py -i UML_example.uml -o example.c,example.h -t ../../templates/C_code.c,../../templates/C_code.h

clean:
	rm -f example.c example.h
