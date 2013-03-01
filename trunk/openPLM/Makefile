RST=rst2html.py
OUTPUT=static/
VPATH=$(OUTPUT)
DIRS=$(wildcard help/*/)

MDIRS=$(patsubst %,static/%,$(DIRS))

RSTS=$(wildcard help/*/*.rst)

HTMLS=$(patsubst %.rst,%.html,$(RSTS))

all: $(MDIRS) $(HTMLS)

clean:
	-rm -rf $(MDIRS)

$(MDIRS):
	@echo $@
	@mkdir -p $@

$(HTMLS): %.html : %.rst $(MDIRS) 
	$(RST) --no-doc-title --link-stylesheet --initial-header-level=3 $< $(OUTPUT)$@


