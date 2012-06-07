# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = _build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean html dirhtml singlehtml pickle json htmlhelp qthelp devhelp epub latex latexpdf text man changes linkcheck doctest

CHDIR_SHELL := $(SHELL)
define chdir
   $(eval _D=$(firstword $(1) $(@D)))
   $(info $(MAKE): cd $(_D)) $(eval SHELL = cd $(_D); $(CHDIR_SHELL))
endef

ifndef $(LANGUAGE)
    LANGUAGE = en
endif

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files named index.html in directories"
	@echo "  singlehtml to make a single large HTML file"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make JSON files"
	@echo "  htmlhelp   to make HTML files and a HTML help project"
	@echo "  qthelp     to make HTML files and a qthelp project"
	@echo "  devhelp    to make HTML files and a Devhelp project"
	@echo "  epub       to make an epub"
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX files and run them through pdflatex"
	@echo "  text       to make text files"
	@echo "  man        to make manual pages"
	@echo "  changes    to make an overview of all changed/added/deprecated items"
	@echo "  linkcheck  to check all external links for integrity"
	@echo "  doctest    to run all doctests embedded in the documentation (if enabled)"
	@echo "To specify a language different than English use somethink like :"
	@echo "make LANGUAGE=fr html"

clean:
	cd $(LANGUAGE) && make clean

tuto:
	cd $(LANGUAGE) && make tuto

oxt:
	cd $(LANGUAGE) && make oxt

dl: tuto oxt

html: dl
	cd $(LANGUAGE) && make html

dirhtml: dl
	cd $(LANGUAGE) && make dirhtml

singlehtml: dl
	cd $(LANGUAGE) && make singlehtml

pickle: dl
	cd $(LANGUAGE) && make pickle

json: dl
	cd $(LANGUAGE) && make json

htmlhelp: dl
	cd $(LANGUAGE) && make htmlhelp

qthelp: dl
	cd $(LANGUAGE) && make qthelp

devhelp: dl
	cd $(LANGUAGE) && make devhelp

epub: dl
	cd $(LANGUAGE) && make epub

latex: dl
	cd $(LANGUAGE) && make latex

latexpdf:
	cd $(LANGUAGE) && make latexpdf

text: dl
	cd $(LANGUAGE) && make text

man: dl
	cd $(LANGUAGE) && make man

changes:
	cd $(LANGUAGE) && make changes

linkcheck:
	cd $(LANGUAGE) && make linkcheck

doctest:
	cd $(LANGUAGE) && make doctest
