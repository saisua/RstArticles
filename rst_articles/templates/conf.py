import sys
from pathlib import Path

sys.path.insert(0, str((Path(__file__).parent.parent / "_ext").resolve()))

extensions = [
	"___1_{extensions}___",
]
bibtex_bibfiles = ['bibliography.bib']
project = "___1_{project}___"
title = "___1_{title}___"
subtitle = "___1_{subtitle}___"
author = "___1_{author}___"
institution = "___1_{institution}___"
numfig = True

dark = ___1_{dark}___  # noqa: E999

if dark:
	background_color = 'black'
	text_color = 'white'
else:
	background_color = None
	text_color = None

title_background_image = None
content_background_image = None
document_class = None

lrst_epilog = '''
.. |today| date::
'''

try:
	with open('title.tex') as f:
		maketitle = f.read()
except FileNotFoundError:
	maketitle = None

try:
	with open('abstract.txt') as f:
		abstract = f.read()
except FileNotFoundError:
	abstract = None

for placeholder, replacement in {
	r'\title': title,
	r'\subtitle': subtitle,
	r'\name': author,
	r'\institution': institution,
	r'\abstract': abstract,
}.items():
	if replacement is not None:
		maketitle = maketitle.replace(
			placeholder,
			replacement
		)

latex_toplevel_sectioning = 'section'

with open('preamble.tex') as f:
	preamble = f.read()

preamble = preamble.replace(
	'___2_{author}___',
	author
).replace(
	'___2_{title}___',
	title
)

if background_color is not None:
	preamble += rf'\pagecolor{{{background_color}}}'

if text_color is not None:
	preamble += rf'\color{{{text_color}}}'

if title_background_image is not None or content_background_image is not None:
	preamble += r'''
\usepackage{background}
\newif\iffirstpage
\firstpagetrue
\backgroundsetup{
  contents={%
	\iffirstpage
'''
	if title_background_image is not None:
		preamble += rf'''
	  \includegraphics[width=\paperwidth,height=\paperheight]{{{title_background_image}}}%
'''
	preamble += r'''
	  \global\firstpagefalse % Disable for all subsequent pages
'''
	if content_background_image is not None:
		preamble += rf'''
	\else
	  \includegraphics[width=\paperwidth,height=\paperheight]{{{content_bg.png}}}%
'''
	preamble += r'''
	\fi
  }
}
'''

latex_elements = {
	'papersize': 'a4paper',
	'pointsize': '11pt',
	'sphinxsetup': f'TitleColor={text_color or "black"},',
	'preamble': preamble,
	'maketitle': maketitle,
	'fncychap': '',
	'extraclassoptions': 'openany',
	'classoptions': r'12pt,english,listoffigures,listoftables,listofalgorithms',
}

if document_class is not None:
	latex_elements['documentclass'] = document_class

# In conf.py
latex_documents = [
	(
		'index',
		'doc.tex',
		project,
		author,
		'manual',
	),
]