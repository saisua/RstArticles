import re
import math

from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.transforms import SphinxTransform

import numpy as np

import sympy


ENV_FORMULA_KEY = 'formula_registry'


class FormulaDefPlaceholder(nodes.General, nodes.Element):
	pass


class FormulaPrintPlaceholder(nodes.General, nodes.Element):
	pass


class FormulaEvalPlaceholder(nodes.General, nodes.Element):
	pass


class FormulaDefDirective(Directive):
	has_content = True
	required_arguments = 1
	optional_arguments = 1
	final_argument_whitespace = True

	def run(self):
		node = FormulaDefPlaceholder()
		signature = self.arguments[0].strip()
		body = '\n'.join(self.content).strip()

		latex_override = (
			self.arguments[1].strip()
			if len(self.arguments) > 1
			else None
		)

		node.attributes['signature'] = signature
		node.attributes['body'] = body
		node.attributes['latex_override'] = latex_override

		return [node]


def fprint_role(role, raw_text, text, lineno, inliner, options={}, content=[]):
	node = FormulaPrintPlaceholder()
	node.attributes['formula_name'] = text
	return [node], []


def feval_role(role, raw_text, text, lineno, inliner, options={}, content=[]):
	node = FormulaEvalPlaceholder()
	node.attributes['eval_call'] = text
	return [node], []


class ResolveFormulas(SphinxTransform):
	default_priority = 999

	def apply(self):
		env = self.document.settings.env
		if not hasattr(env, ENV_FORMULA_KEY):
			setattr(env, ENV_FORMULA_KEY, {})
		registry = getattr(env, ENV_FORMULA_KEY)

		for node in self.document.traverse(FormulaDefPlaceholder):
			signature = node.attributes.get('signature', '')
			body = node.attributes.get('body', '')
			latex_manual = node.attributes.get('latex_override')

			match = re.match(r'^\s*([a-zA-Z_]\w*)\((.*?)\)$', signature)

			if match and body:
				name = match.group(1).strip()
				args = [a.strip() for a in match.group(2).split(',') if a.strip()]

				if latex_manual:
					latex_repr = latex_manual
				else:
					latex_repr = sympy.latex(sympy.sympify(body))

				# print(name, latex_repr)

				registry[name] = {
					'args': args,
					'body': body,
					'latex': latex_repr
				}
				node.parent.remove(node)
			else:
				node.replace_self(nodes.problematic("", f"Invalid formula: {signature}"))

		for node in self.document.traverse(FormulaPrintPlaceholder):
			name = node.attributes['formula_name'].strip().rstrip('()')

			if name in registry:
				latex_code = registry[name]['latex']
				new_node = nodes.math(latex_code, latex_code)

				node.replace_self(new_node)
			else:
				node.replace_self(nodes.problematic("", f"Formula not found: {name}"))

		for node in self.document.traverse(FormulaEvalPlaceholder):
			call_text = node.attributes['eval_call'].strip()
			match = re.match(r'^\s*([a-zA-Z_]\w*)\((.*?)\)$', call_text)

			if match:
				name, args_str = match.group(1).strip(), match.group(2).strip()
				if name in registry:
					f_info = registry[name]
					try:
						passed_args = eval(f"({args_str},)" if args_str else "()")

						context = dict(zip(f_info['args'], passed_args))
						local_vars = dict()

						if np is not None:
							local_vars.update(np.__dict__)
						for k, v in math.__dict__.items():
							if k not in local_vars:
								local_vars[k] = v

						local_vars["__builtins__"] = dict()

						result = eval(
							f_info['body'],
							local_vars,
							context,
						)

						node.replace_self(nodes.Text(str(result)))
					except Exception as e:
						node.replace_self(nodes.problematic("", f"Eval error: {e}"))
				else:
					node.replace_self(nodes.problematic("", f"Formula not found: {name}"))


def setup(app):
	app.add_node(FormulaDefPlaceholder)
	app.add_node(FormulaPrintPlaceholder)
	app.add_node(FormulaEvalPlaceholder)

	app.add_directive('fdef', FormulaDefDirective)

	app.add_role('fprint', fprint_role)
	app.add_role('feval', feval_role)

	app.add_post_transform(ResolveFormulas)

	return {
		'version': '0.2',
		'parallel_read_safe': True
	}
