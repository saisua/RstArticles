from pathlib import Path
from dataclasses import dataclass, field

from language_tool_python import LanguageTool

from doc8 import doc8


from .extractor.rst import rst_to_text


@dataclass
class RSTLinter:
	language: str

	syntax_errors: list = field(default_factory=list)
	language_errors: list = field(default_factory=list)

	custom_dictionary: set[str] = field(default_factory=set)

	tool: LanguageTool | None = field(default=None)

	def __post_init__(self):
		self.tool = LanguageTool(self.language)

	def lint_syntax(self, file_path: Path | str):
		self.syntax_errors.clear()

		if isinstance(file_path, Path):
			file_path = str(file_path)

		syntax_result = doc8(paths=[file_path])
		if syntax_result.total_errors:
			for error, file, line, code, desc in syntax_result.errors:
				self.syntax_errors.append((line, desc))

	def lint_language(self, content: str, *, content_extension: str = ".rst"):
		self.language_errors.clear()

		if content_extension == ".rst":
			clean_text = rst_to_text(content)
		else:
			clean_text = content

		matches = self.tool.check(clean_text)

		if matches:
			for error in matches:
				actual_error = error.context[
					error.offset_in_context:
					error.offset_in_context + error.error_length
				]

				if actual_error.strip().lower() not in self.custom_dictionary:
					self.language_errors.append((
						actual_error,
						error.message,
						error.context,
						error.replacements,
					))

	def print_syntax_errors(self):
		for line, desc in self.syntax_errors:
			print(line, '|', desc)

	def print_language_errors(self):
		for actual_error, msg, context, suggestions in self.language_errors:
			print(
				f"{msg} in \"{actual_error}\":\n\t{context}\n\t"
				f"Suggestions: {' | '.join(suggestions[:3])}"
			)

	def print_errors(self, *, print_info: bool = True):
		if len(self.syntax_errors):
			if print_info:
				print("# Syntax errors #")
			self.print_syntax_errors()
		elif print_info:
			print("+ No syntax errors")

		if len(self.language_errors):
			if print_info:
				print("\n# Language errors #")
			self.print_language_errors()
		elif print_info:
			print("+ No language errors")
