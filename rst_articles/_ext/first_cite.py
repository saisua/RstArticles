from docutils import nodes


ENV_CITE_KEY = 'first_cite_counter'


def first_cite(role, rawtext, text, lineno, inliner, options={}, content=[]):
    env = inliner.document.settings.env.app.env

    if not hasattr(env, ENV_CITE_KEY):
        setattr(env, ENV_CITE_KEY, set())

    added_texts = getattr(env, ENV_CITE_KEY)

    if text not in added_texts:
        added_texts.add(text)

        cite_node = nodes.citation_reference(rawtext, text, refname=text)

        return [cite_node], []

    else:
        return [], []


def setup(app):
    app.add_role('fcite', first_cite)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
