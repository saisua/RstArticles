from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.writers.latex import LaTeXTranslator
from sphinx.util.docutils import SphinxDirective


class floating_figure(nodes.General, nodes.Element):
	pass


class FloatingFigureDirective(SphinxDirective):
	required_arguments = 1
	optional_arguments = 0
	final_argument_whitespace = True
	has_content = True

	option_spec = {
		'name': directives.unchanged,
		'width': directives.unchanged,
		'height': directives.unchanged,
		'align': lambda x: directives.choice(x, ('right', 'left', 'center')),
	}

	def run(self):
		caption_text = '\n'.join(self.content)

		caption_nodes, messages = self.state.inline_text(
			caption_text,
			self.lineno
		)

		caption_node = nodes.caption(caption_text, '', *caption_nodes)

		image_uri = self.arguments[0]
		name = self.options.get('name')
		width = self.options.get('width')
		height = self.options.get('height')
		align = self.options.get('align', 'center')

		image_options = {'uri': image_uri, 'width': width, 'height': height}
		image_node = nodes.image(**image_options)

		figure_node = floating_figure()
		figure_node['uri'] = image_uri
		figure_node['name'] = name
		figure_node['width'] = width
		figure_node['height'] = height
		figure_node['align'] = align

		figure_node.append(image_node)
		figure_node.append(caption_node)

		result_nodes = [figure_node] + messages
		if name:
			targetid = name
			targetnode = nodes.target('', '', names=[targetid])
			self.state.document.note_explicit_target(targetnode)
			result_nodes.insert(0, targetnode)

		return result_nodes


def visit_floating_figure_latex(self: LaTeXTranslator, node: floating_figure):
	'''Generates LaTeX for the custom floating-figure node using 'wrapfig'.'''

	align_map = {'right': 'r', 'left': 'l', 'center': 'l'}
	alignment_code = align_map.get(node['align'], 'r')

	width = node.get('width', '100%').strip()

	try:
		if width.endswith('%'):
			width_ratio = float(width[:-1]) / 100.0
		else:
			width_ratio = float(width)
		latex_width = f'{width_ratio:.2f}\\linewidth'

		height = node.get('height')
		height_option = f',height={height}' if height else ''

		# graphic_options = f'width={latex_width}{height_option}'
		graphic_options = f'width=\\linewidth{height_option}'

	except (ValueError, TypeError):
		width = node.get('width', '0.5\\linewidth')
		graphic_options = f'width={width}'
		height = node.get('height')
		if height:
			graphic_options += f',height={height}'

		latex_width = width

	self.body.append(
		f'\\begin{{wrapfigure}}{{{alignment_code}}}{{{latex_width}}}\n'
	)

	r'''
	\phantomsection\label{\detokenize{lorem:lorem-figure}}
	\begin{wrapfigure}{r}{0.50\linewidth}
	\centering % Optional: to center the image if smaller than \linewidth
	\includegraphics[width=\linewidth]{img.jpg}
	\caption{My caption. \label{figure:lorem_figure}}
	\end{wrapfigure}
	'''

	if node['align'] == 'center':
		self.body.append('\\centering\n')

	image_uri = node.get('uri')
	if image_uri:
		self.body.append(f'\\includegraphics[{graphic_options}]{{{image_uri}}}\n')
	else:
		self.body.append('% Missing image URI\n')

	caption_node = node.children[1]

	label_text = ''
	if node.get('name'):
		label_text = f'\\label{{figure:{node["name"]}}}'

	start_len = len(self.body)

	for child in caption_node.children:
		child.walkabout(self)

	caption_content = ''.join(self.body[start_len:])

	del self.body[start_len:]

	self.body.append(f'\\caption{{{caption_content.strip()} {label_text}}}\n')
	raise nodes.SkipNode


def depart_floating_figure_latex(self: LaTeXTranslator, node: floating_figure):
	self.body.append('\\end{wrapfigure}\n')


def setup(app):
	app.add_node(
		floating_figure,
		latex=(visit_floating_figure_latex, depart_floating_figure_latex)
	)
	app.add_directive('floating-figure', FloatingFigureDirective)
	app.add_latex_package('wrapfig')

	return {
		'version': '0.2',
		'parallel_read_safe': True,
		'parallel_write_safe': True,
	}
