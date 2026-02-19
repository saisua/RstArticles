import re

from docutils import nodes
from docutils.core import publish_doctree


inline_rst_call = re.compile(r'([ \t]+)?(?:\s*:[a-z]+:`[^`]+`)+([ \t]+)?')
ends_s = re.compile(r'.*?\s$', re.MULTILINE | re.DOTALL)
starts_s = re.compile(r'^\s.*', re.MULTILINE | re.DOTALL)


class PlainTextExtractor(nodes.NodeVisitor):
	def __init__(self, document):
		super().__init__(document)
		self.found_text = []

	def visit_Text(self, node):
		current = node
		while current:
			if isinstance(current, nodes.system_message):
				return
			current = current.parent

		clean_text = inline_rst_call.sub(
			lambda match: ' ' if match.group(1) or match.group(2) else '',
			node.astext()
		)

		if not clean_text.strip(' \n.'):
			return

		self.found_text.append(clean_text)
		# print(node.astext())
		# print('->', self.found_text[-1], '\n---')

	def depart_Text(self, node):
		pass

	def unknown_visit(self, node):
		pass

	def unknown_departure(self, node):
		pass


def rst_to_text(rst_content: str) -> str:
	doctree = publish_doctree(
		rst_content,
		settings_overrides={
			'report_level': 5,
			'halt_level': 5,
			'exit_status_level': 5
		}
	)

	visitor = PlainTextExtractor(doctree)
	doctree.walkabout(visitor)

	found_text = visitor.found_text

	clean_text = [str(found_text[0])]
	for text in map(str, found_text[1:]):
		prev_ends = ends_s.match(clean_text[-1])
		curr_starts = starts_s.match(text)

		if prev_ends and curr_starts:
			clean_text.append(text[1:])
		elif not (prev_ends or curr_starts):
			clean_text.append(f" {text}")
		else:
			clean_text.append(text)

	return "".join(clean_text)
