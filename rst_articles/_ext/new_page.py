from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.writers.latex import LaTeXTranslator
from sphinx.util.docutils import SphinxDirective


class new_page(nodes.General, nodes.Element):
	pass


class NewPageDirective(SphinxDirective):
	required_arguments = 0
	optional_arguments = 0
	final_argument_whitespace = True
	has_content = True

	option_spec = {
		'pages': directives.unchanged,
	}

	def run(self):
		n_pages = int(self.options.get('pages', '1'))

		return [new_page({'pages': n_pages})]


def visit_new_page_latex(self: LaTeXTranslator, node: new_page):
	n_pages = node.rawsource['pages']

	for _ in range(n_pages):
		self.body.append('\\newpage\n')

	raise nodes.SkipNode


def depart_new_page_latex(self: LaTeXTranslator, node: new_page):
	pass


def setup(app):
	app.add_node(
		new_page,
		latex=(visit_new_page_latex, depart_new_page_latex)
	)

	app.add_directive('new-page', NewPageDirective)

	return {
		'version': '0.2',
		'parallel_read_safe': True,
		'parallel_write_safe': True,
	}
