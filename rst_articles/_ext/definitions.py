import re
from pathlib import Path
from dataclasses import dataclass

import wikipedia

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.util.docutils import SphinxDirective
from sphinx.transforms import SphinxTransform


ENV_DEFS_KEY = 'definitions'
ENV_SEEN_KEY = 'seen_abbreviations'
DEF_PATH = Path('source/definitions')
DEF_PATH.mkdir(parents=True, exist_ok=True)

wiki_ref_pattern = re.compile(r'(\[\d+\]|\u200B)')
def_sent_pattern = re.compile(r'\.[^\.]')


@dataclass
class Definition:
	short: str
	long: str
	search: str
	language: str
	max_sentences: int
	description: str


class DefinitionListPlaceholder(nodes.General, nodes.Element):
	pass


class AbbrevPlaceholder(nodes.General, nodes.Element):
	pass


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
			short=self.options.get('short', abb),
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
			max_sentences=int(self.options.get(
				'max_sentences',
				self.options.get('max_sents', 0)
			)),
		)
		return []


def abbrev_role(role, raw_text, text, lineno, inliner, options={}, content=[]):
	node = AbbrevPlaceholder()
	node.attributes['key'] = text
	node.attributes['raw_text'] = raw_text
	return [node], []


class ResolveDefinitions(SphinxTransform):
	default_priority = 111

	def apply(self):
		env = self.document.settings.env
		defs = getattr(env, ENV_DEFS_KEY)
		if not hasattr(env, ENV_SEEN_KEY):
			setattr(env, ENV_SEEN_KEY, set())
		registry = getattr(env, ENV_SEEN_KEY)

		for node in self.document.traverse(AbbrevPlaceholder):
			key = node.attributes['key']
			d = defs.get(key)
			if not d:
				node.replace_self(nodes.problematic('', key))
				continue

			if key not in registry and d.long:
				label = f"{d.long} ({d.short})"
				registry.add(key)
			else:
				label = d.short
			node.replace_self(nodes.Text(label))


class ResolveDefinitionList(SphinxTransform):
	default_priority = 999

	def apply(self):
		env = self.document.settings.env
		if not hasattr(env, ENV_DEFS_KEY):
			setattr(env, ENV_DEFS_KEY, dict())
		defs = getattr(env, ENV_DEFS_KEY)

		for node in self.document.traverse(DefinitionListPlaceholder):
			if not defs:
				node.replace_self(nodes.problematic("", "No definitions found"))
				continue

			dl = nodes.definition_list()
			for key, d in defs.items():
				desc = self._get_description(d)
				if desc is None:
					continue

				term_text = f"{d.long} ({d.short})" if d.long else d.short
				li = nodes.definition_list_item()
				li += nodes.term('', term_text)
				li += nodes.definition('', nodes.paragraph('', desc))
				dl += li
			node.replace_self(dl)

	def _get_description(self, d):
		if d.description:
			return d.description

		if d.search is None:
			return None

		cache_file = DEF_PATH / f"{d.search.replace('/', '_')}.txt"

		if cache_file.exists():
			text = cache_file.read_text()
		else:
			wikipedia.set_lang(d.language)
			text = wikipedia.summary(d.search)
			text = wiki_ref_pattern.sub('', text).replace('\n', ' ').strip()
			cache_file.write_text(text)

		if d.max_sentences > 0:
			matches = list(def_sent_pattern.finditer(text))
			if len(matches) >= d.max_sentences:
				text = text[:matches[d.max_sentences - 1].end() - 1]
		return text


def setup(app):
	app.add_node(AbbrevPlaceholder)
	app.add_node(DefinitionListPlaceholder)

	app.add_directive('new-def', NewDefinitionDirective)
	app.add_directive('definitions', lambda *_: [DefinitionListPlaceholder()])

	app.add_role('abbrev', abbrev_role)

	app.add_post_transform(ResolveDefinitions)
	app.add_post_transform(ResolveDefinitionList)
	return {
		'version': '0.1',
		'parallel_read_safe': False,
		'parallel_write_safe': True,
	}
