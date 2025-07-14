.PHONY: all clean

all: fig.pdf fig.dvi fig.svg

fig.pdf: *.tex
	lualatex --output-format=pdf fig.tex

fig.dvi: *.tex
	lualatex --output-format=dvi fig.tex

fig.svg: fig.dvi
	dvisvgm --font-format=woff fig.dvi

clean:
	rm -f *.aux *.log *.out *.ps *.pdf *.dvi *.svg
