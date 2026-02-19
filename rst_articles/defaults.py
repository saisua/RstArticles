from pathlib import Path


external_extensions = {
	'sphinxcontrib.bibtex',
}

custom_extensions = set()
for extension in Path('rst_articles/_ext').glob('*.py'):
	name = extension.name
	if name.startswith('_'):
		continue

	if name.endswith('.py'):
		name = name[:-3]

	custom_extensions.add(name)

default_extensions = external_extensions | custom_extensions
