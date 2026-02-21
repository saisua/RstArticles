from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field
from functools import partial
import subprocess
import shutil

try:
	from pdf2image import convert_from_path
	from IPython.display import display
except ImportError:
	convert_from_path = None
	display = None

from rst_articles.defaults import default_extensions


try:
	from rst_articles.linter import RSTLinter
except ImportError:
	RSTLinter = None


pdir = Path(__file__).parent.parent
_base_ext_path: Path = pdir / "_ext"


@dataclass
class Article:
	cwd: Path = field(default_factory=Path)
	extensions: set[str] = field(default_factory=partial(set, default_extensions))
	enable_linter: bool = field(default=True)
	linter_lang: str = field(default='en-US')

	source_dir: Path = field(default=Path('source'))
	build_dir: Path = field(default=Path('build'))

	linter: Optional[RSTLinter] = field(default=None)

	_custom_dictionary: set[str] = field(default_factory=set)

	_index_template: str = field(default=None)
	_bibliography_template: str = field(default=None)
	_definition_list_template: str = field(default=None)
	_config_template: str = field(default=None)
	_title_template: str = field(default=None)
	_preamble_template: str = field(default=None)

	_ext_path: Path = Path('_ext')

	sphinx_logs: str = field(default='')
	latex_logs: str = field(default='')

	def __post_init__(self):
		self.set_abstract = partial(
			self.write,
			"abstract.txt",
			enable_syntax_linting=False,
			enable_language_linting=True,
		)
		if self.enable_linter and RSTLinter is not None:
			self.linter = RSTLinter(
				self.linter_lang,
				custom_dictionary=self._custom_dictionary,
			)
			self.print_errors = self.linter.print_errors

		self.reload_templates()

		if (self.source_dir / "custom_dictionary.txt").exists():
			with open(self.source_dir / "custom_dictionary.txt", "r") as f:
				new_words = f.readlines()
			self.add_custom_words(*new_words)

	@staticmethod
	def reload_templates():
		with open(pdir / "templates" / "index.rst", "r") as f:
			Article._index_template = f.read()
		with open(pdir / "templates" / "bibliography.rst", "r") as f:
			Article._bibliography_template = f.read()
		with open(pdir / "templates" / "definition_list.rst", "r") as f:
			Article._definition_list_template = f.read()
		with open(pdir / "templates" / "conf.py", "r") as f:
			Article._config_template = f.read()
		with open(pdir / "templates" / "title.tex", "r") as f:
			Article._title_template = f.read()
		with open(pdir / "templates" / "preamble.tex", "r") as f:
			Article._preamble_template = f.read()

	def reload_extensions(self):
		self._ext_path.mkdir(parents=True, exist_ok=True)
		for _ext_file in _base_ext_path.glob("*.py"):
			shutil.copy(
				_ext_file,
				self._ext_path / _ext_file.name
			)

	def add_custom_words(self, *words: str):
		self._custom_dictionary.update(filter(bool, (
			word.strip().lower()
			for word in words
		)))

		with open(self.source_dir / "custom_dictionary.txt", "w+") as f:
			f.write("\n".join(self._custom_dictionary))

	def set_config(
		self,
		project: str,
		title: str,
		subtitle: str,
		author: str,
		institution: str,
		dark: bool,
		*,
		extensions: set[str] = default_extensions,
		base: Optional[Path] = None,
		definitions: str = "definitions.rst",
		definition_list: str = "definition_list.rst",
		bibliography: str = "bibliography.bib",
	):
		if base is None:
			base = self.source_dir

		assert '"' not in project, "Project name cannot contain quotes"
		assert '"' not in title, "Title cannot contain quotes"
		assert '"' not in subtitle, "Subtitle cannot contain quotes"
		assert '"' not in author, "Author cannot contain quotes"
		assert '"' not in institution, "Institution cannot contain quotes"
		assert str(dark) in ('True', 'False'), "Dark mode must be a boolean"
		assert not any((
			'"' in ext
			for ext in extensions
		)), "Extensions cannot contain quotes"

		self.reload_extensions()

		self.write(
			"title.tex",
			Article._title_template,
			base=base,
			enable_linter=False,
			add_fname_title=False,
		)
		self.write(
			"preamble.tex",
			Article._preamble_template,
			base=base,
			enable_linter=False,
			add_fname_title=False,
		)
		self.write(
			"conf.py",
			Article._config_template.replace(
				'___1_{extensions}___',
				"\",\n\t\"".join(extensions)
			).replace(
				'___1_{project}___',
				project
			).replace(
				'___1_{title}___',
				title
			).replace(
				'___1_{subtitle}___',
				subtitle
			).replace(
				'___1_{author}___',
				author
			).replace(
				'___1_{institution}___',
				institution
			).replace(
				'___1_{dark}___',
				'True' if dark else 'False'
			),
			base=base,
			enable_linter=False,
			add_fname_title=False,
		)
		if not (base / definitions).exists():
			self.write(
				definitions, "",
				base=base,
				enable_linter=False,
				add_fname_title=False,
			)
		if not (base / definition_list).exists():
			self.write(
				definition_list, "",
				base=base,
				enable_linter=False,
				add_fname_title=False,
			)
		if not (base / bibliography).exists():
			self.write(
				bibliography, "",
				base=base,
				enable_linter=False,
				add_fname_title=False,
			)

	def set_index(
		self,
		*files: Path | str,
		fname: Path | str = "index.rst",
		base: Optional[Path] = None,
		definitions: str = "definitions.rst",
		definition_list: str = "definition_list.rst",
		bibliography: str = "bibliography.rst",
	):
		if base is None:
			base = self.source_dir

		index = [Article._index_template.format(toctree="\n\t".join(files))]

		if not index[0].endswith("\n"):
			index.append('')

		if definitions:
			index.append(f".. include:: {definitions}")
		if definition_list:
			index.append(f".. include:: {definition_list}")
		if bibliography:
			index.append(f".. include:: {bibliography}")

		if len(index) == 1:
			index = index[0]
		else:
			index = "\n".join(index)

		self.write(
			fname,
			index,
			base=base,
			enable_linter=False,
			add_fname_title=True,
		)

	def set_bibliography(
		self,
		content: str,
		*,
		fname: Path | str = "bibliography.bib",
		base: Optional[Path] = None,
		enable_linter: bool = None,
		style: str = "unsrt",
	):
		if base is None:
			base = self.source_dir

		self.write(
			"bibliography.rst",
			Article._bibliography_template.format(style=style),
			base=base,
			enable_linter=enable_linter,
			add_fname_title=False,
		)
		self.write(
			fname,
			content,
			base=base,
			enable_linter=False,
			add_fname_title=False,
		)

	def set_definitions(
		self,
		content: str,
		*,
		fname: Path | str = "definitions.rst",
		base: Optional[Path] = None,
		enable_linter: bool = None,
	):
		if base is None:
			base = self.source_dir

		self.write(
			"definition_list.rst",
			Article._definition_list_template,
			base=base,
			enable_linter=enable_linter,
			add_fname_title=False,
		)
		self.write(
			fname,
			content,
			base=base,
			enable_linter=enable_linter,
			add_fname_title=False,
		)

	def write(
		self,
		file: Path | str,
		content: str,
		*,
		base: Optional[Path] = None,
		enable_linter: bool = True,
		enable_syntax_linting: bool = True,
		enable_language_linting: bool = True,
		raise_on_error: bool = False,
		add_fname_title: bool = False,
	):
		if base is None:
			base = self.source_dir

		if base is not None:
			file = base / file
		elif not isinstance(file, Path):
			file = Path(file)

		file.parent.mkdir(
			parents=True,
			exist_ok=True,
		)

		content = content.strip('\n')

		if file.suffix == '.rst':
			if add_fname_title:
				content = f"{file.stem.upper()}\n{'^' * len(file.stem)}\n\n{content}\n"
			else:
				content = f"{content}\n"

		lang_errors = syn_errors = False

		if (enable_linter and enable_language_linting and self.linter is not None):
			self.linter.lint_language(
				content,
				content_extension=file.suffix
			)
			if len(self.linter.language_errors):
				if raise_on_error:
					self.linter.print_language_errors()
					raise ValueError("Language errors found")
				lang_errors = True
		else:
			self.linter.language_errors.clear()

		with open(file, 'w') as f:
			f.write(content)

		if (enable_linter and enable_syntax_linting and self.linter is not None):
			self.linter.lint_syntax(file)
			if len(self.linter.syntax_errors):
				if raise_on_error:
					self.print_errors()
					raise ValueError("Syntax errors found")
				syn_errors = True
		else:
			self.linter.syntax_errors.clear()

		if syn_errors or lang_errors:
			self.print_errors()

	def build(
		self,
		*,
		source_dir: Optional[Path] = None,
		build_dir: Optional[Path] = None,
		log_file: Optional[Path] = None,
	):
		if source_dir is None:
			source_dir = self.source_dir

		if build_dir is None:
			build_dir = self.build_dir

		if log_file is None:
			log_file = build_dir / "doc.log"

		sphinx_result = subprocess.run(
			[
				'sphinx-build',
				'-b', 'latex',
				'-j', 'auto',
				'-E',
				source_dir,
				build_dir
			],
			check=False,
			capture_output=True,
			text=True
		)

		self.sphinx_logs = f"""
[Sphinx STDOUT]
{sphinx_result.stdout.strip()}
[Sphinx STDERR]
{sphinx_result.stderr.strip()}
"""
		if sphinx_result.returncode != 0:
			print(
				"Error: Sphinx build failed "
				f"(Return code {sphinx_result.returncode}). Aborting."
			)
			print(self.sphinx_logs)
		else:
			make_result = subprocess.run(
				['make', '-j', '8', '--silent'],
				cwd=build_dir,
				capture_output=True,
				text=True,
				check=False
			)

			try:
				with open(log_file, 'r') as f:
					self.latex_logs = f.read()
			except Exception as e:
				self.latex_logs = f"An exception occurred: {e}"

			if make_result.returncode != 0:
				print("\nXXXXXXXXXXXX")
				print(">>> BEGIN DOC.LOG CONTENT (make failed) <<<")
				print(self.latex_logs)
				print(">>> END DOC.LOG CONTENT <<<")
			else:
				print("Generated PDF at:", build_dir / "doc.pdf")
				print("Generated LaTeX at:", build_dir / "doc.tex")

	def render_pdf(
		self,
		*,
		build_dir: Optional[Path] = None,
		show_page: Optional[int] = None,
	):
		if build_dir is None:
			build_dir = self.build_dir

		if convert_from_path is None or display is None:
			raise ImportError("pdf2image and IPython are required to render the PDF")

		image = None
		for ii, image in enumerate(
			convert_from_path(
				build_dir / "doc.pdf"
			)
		):
			if show_page is None or show_page == ii:
				display(image)

		if image is not None:
			del image
