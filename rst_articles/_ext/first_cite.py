from docutils import nodes

from sphinx.transforms import SphinxTransform


ENV_CITE_KEY = 'first_cite_counter'


class FirstCitePlaceholder(nodes.General, nodes.Element):
    pass


def first_cite_role(
    role,
    raw_text,
    text,
    lineno,
    inliner,
    options={},
    content=[],
):
    node = FirstCitePlaceholder()

    node.attributes['cite_key'] = text
    node.attributes['raw_text'] = raw_text

    return [node], []


class ResolveFirstCites(SphinxTransform):
    default_priority = 999

    def apply(self):
        env = self.document.settings.env
        if not hasattr(env, ENV_CITE_KEY):
            setattr(env, ENV_CITE_KEY, set())
        registry = getattr(env, ENV_CITE_KEY)

        # cmd = ""
        # while cmd != 'exit':
        #     exec(cmd := input('> '))

        citation_domain = env.get_domain("cite")
        print(citation_domain)

        for node in self.document.traverse(FirstCitePlaceholder):
            key = node.attributes['cite_key']

            if key not in registry:
                registry.add(key)

                for citation in citation_domain.citations:
                    if citation.key == key:
                        citation_id = citation.citation_id
                        break
                else:
                    node.replace_self(nodes.problematic("", f"Citation not found: {key}"))
                    continue

                new_node = nodes.citation_reference(
                    node.attributes['raw_text'],
                    key,
                    refname=citation_id,
                    docname=self.env.docname,
                )
                node.replace_self(new_node)
            else:
                node.replace_self(nodes.Text(""))


def setup(app):
    app.add_node(FirstCitePlaceholder)
    app.add_role('fcite', first_cite_role)
    app.add_post_transform(ResolveFirstCites)

    return {
        'version': '0.1',
        'parallel_read_safe': False,
        'parallel_write_safe': True,
    }
