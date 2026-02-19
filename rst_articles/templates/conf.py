import sys
from pathlib import Path

sys.path.insert(0, str((Path(__file__).parent.parent / "_ext").resolve()))

extensions = [
	"___{extensions}___",
]
bibtex_bibfiles = ['bibliography.bib']
project = "___{project}___"
title = "___{title}___"
subtitle = "___{subtitle}___"
author = "___{author}___"
institution = "___{institution}___"
numfig = True

dark = ___{dark}___  # noqa: E999

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

preamble = r'''
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}

\usepackage{fancyhdr}
\pagestyle{fancy}
\makeatletter
\fancypagestyle{normal}{
	\fancyhf{} % Clear all headers/footers
	% Set the header content:
	% RO/LE: Right Odd / Left Even page header
	% Use \py@HeaderFamily for the default Sphinx font style
	% \nouppercase{} prevents capitalization of the chapter/section name
	% \rightmark is the current section/chapter title
	\fancyhead[RO,LE]{{\py@HeaderFamily ''' + author + r'''}} % Left-Even Header: Author Name
	\fancyhead[LO,RE]{{\py@HeaderFamily ''' + title + r'''}} % Right-Odd Header: Current Chapter/Part title
	% Set the footer content (e.g., page number)
	\fancyfoot[RO,LE]{{\py@HeaderFamily \thepage}} % Right-Odd/Left-Even Footer: Page Number
	\fancyfoot[LO,RE]{{\py@HeaderFamily \nouppercase{\rightmark}}} % Right-Odd Header: Current Chapter/Part title
	\renewcommand{\headrulewidth}{0.4pt} % Re-add the header rule (line)
	\renewcommand{\footrulewidth}{0.4pt} % Remove the footer rule
}
\fancypagestyle{plain}{
	\fancyhf{} % Clear all headers/footers
	\fancyfoot[RO,LE]{{\py@HeaderFamily \thepage}} % Just the page number in the footer
	\renewcommand{\headrulewidth}{0pt} % Remove header rule
	\renewcommand{\footrulewidth}{0pt} % Remove footer rule
}
\makeatother

\usepackage{chngcntr}
\counterwithout{section}{chapter}
\setcounter{section}{0}
'''

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