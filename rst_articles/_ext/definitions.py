from pathlib import Path
from dataclasses import dataclass
import re

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

import wikipedia


ENV_ABB_KEY = 'abbreviation_long_text_counter'
ENV_DEFS_KEY = 'definitions'


wiki_ref_pattern = re.compile(r'(\[\d+\]|\u200B)')
def_sent_pattern = re.compile(r'\.[^\.]')

definitions_path = Path('source', 'definitions')
definitions_path.mkdir(exist_ok=True)


@dataclass
class Definition:
	short: str | None
	long: str | None
	description: str | None
	search: str | None
	language: str | None
	max_sentences: int | None


class DefinitionList(nodes.Element):
	pass


class NewDefinitionListDirective(SphinxDirective):
	required_arguments = 0
	optional_arguments = 0
	final_argument_whitespace = True
	has_content = False

	option_spec = {}

	def run(self):
		return [DefinitionList()]


class NewDefinitionDirective(SphinxDirective):
	required_arguments = 1
	optional_arguments = 0
	final_argument_whitespace = True
	has_content = False

	option_spec = {
		'search': directives.unchanged,
		'lang': directives.unchanged,
		'language': directives.unchanged,
		'short': directives.unchanged,
		'long': directives.unchanged,
		'description': directives.unchanged,
		'desc': directives.unchanged,
		'max_sents': directives.unchanged,
		'max_sentences': directives.unchanged,
	}

	def run(self):
		env = self.env

		if not hasattr(env, ENV_DEFS_KEY):
			setattr(env, ENV_DEFS_KEY, dict())

		definitions = getattr(env, ENV_DEFS_KEY)

		abb = self.arguments[0]

		definitions[abb] = Definition(
			short=self.options.get('short'),
			long=self.options.get('long'),
			description=self.options.get(
				'description',
				self.options.get('desc')
			),
			search=self.options.get('search'),
			language=self.options.get(
				'language',
				self.options.get('lang')
			),
			max_sentences=self.options.get(
				'max_sentences',
				self.options.get('max_sents')
			),
		)

		return []


def show_abbreviation(
	role,
	rawtext,
	text,
	lineno,
	inliner,
	options: dict = {},
	content: list = []
):
	env = inliner.document.settings.env.app.env

	if not hasattr(env, ENV_DEFS_KEY):
		err = nodes.literal(rawtext, "No definitions")
		return [err], []

	definitions = getattr(env, ENV_DEFS_KEY)
	definition = definitions.get(text)

	if definition is None:
		err = nodes.literal(rawtext, f"No definition for {text}")
		return [err], []

	if not hasattr(env, ENV_ABB_KEY):
		setattr(env, ENV_ABB_KEY, set())

	added_texts = getattr(env, ENV_ABB_KEY)

	short = definition.short or text

	if definition.long is not None and text not in added_texts:
		added_texts.add(text)

		abbreviation = nodes.literal(rawtext, f"{definition.long} ({short})")
	else:
		abbreviation = nodes.literal(rawtext, short)

	return [abbreviation], []


def delayed_definition_list(app, doctree, docname):
	for node in doctree.findall(DefinitionList):
		env = app.env

		if not hasattr(env, ENV_DEFS_KEY):
			setattr(env, ENV_DEFS_KEY, dict())

		definitions = getattr(env, ENV_DEFS_KEY)

		if not len(definitions):
			print("No definitions")
			node.replace_self([
				nodes.literal("No_definitions_text", "Definitions is empty")
			])
			continue

		# TODO: Add plain page type

		definition_list = nodes.definition_list()
		for abb, defi in definitions.items():
			description = defi.description
			if description is None and defi.search is not None:
				stored_def = definitions_path / f"{defi.search.replace('/', '_')}.txt"

				print(defi.search)

				if stored_def.exists():
					with open(stored_def, 'r') as f:
						description = f.read()
				else:
					if defi.language is not None:
						wikipedia.set_lang(defi.language)

					description = wiki_ref_pattern.sub(
						'',
						str(wikipedia.summary(defi.search))
					).replace('\n', ' ').strip()

					with open(stored_def, 'w') as f:
						f.write(description)

			if description is None:
				continue

			if defi.max_sentences is not None:
				max_sents = int(defi.max_sentences)
				sent_matches = list(def_sent_pattern.finditer(description))

				if len(sent_matches) > max_sents:
					nth_sentence_end_match = sent_matches[max_sents - 1]

					cut_off_index = nth_sentence_end_match.end() - 1

					description = description[:cut_off_index]

			if defi.long:
				if defi.short or abb:
					long = f"{defi.long} ({defi.short or abb})"
				else:
					long = defi.long
			else:
				long = defi.short or abb

			list_item = nodes.definition_list_item()

			list_item += nodes.term('', long)

			description_text = nodes.paragraph(description, description)
			definition = nodes.definition('', description_text)
			list_item += definition

			definition_list += list_item

		node.replace_self(definition_list)


def latex_noop_visit(self, node):
	pass


def latex_noop_depart(self, node):
	pass


def purge_definitions(app, env, docname):
	pass


def merge_definitions(app, env, docnames, other):
	if not hasattr(env, ENV_DEFS_KEY):
		setattr(env, ENV_DEFS_KEY, dict())

	if hasattr(other, ENV_DEFS_KEY):
		env_definitions = getattr(env, ENV_DEFS_KEY)
		other_definitions = getattr(other, ENV_DEFS_KEY)

		env_definitions.update(other_definitions)


def setup(app):
	app.add_directive('definitions', NewDefinitionListDirective)
	app.add_directive('new-def', NewDefinitionDirective)

	app.add_role('abbrev', show_abbreviation)

	app.add_node(
		DefinitionList,
		latex=(latex_noop_visit, latex_noop_depart)
	)

	app.connect('env-purge-doc', purge_definitions)
	app.connect('env-merge-info', merge_definitions)

	app.connect('doctree-resolved', delayed_definition_list)

	return {
		'version': '0.2',
		'parallel_read_safe': True,
		'parallel_write_safe': True,
	}
