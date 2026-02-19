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

with open(pdir / "templates" / "index.rst", "r") as f:
	index_template = f.read()
with open(pdir / "templates" / "bibliography.rst", "r") as f:
	bibliography_template = f.read()
with open(pdir / "templates" / "definition_list.rst", "r") as f:
	definition_list_template = f.read()
with open(pdir / "templates" / "conf.py", "r") as f:
	config_template = f.read()
with open(pdir / "templates" / "title.tex", "r") as f:
	title_template = f.read()
_ext_path = pdir / "_ext"


@dataclass
class Article:
	cwd: Path = field(default_factory=Path)
	extensions: set[str] = field(default_factory=partial(set, default_extensions))
	enable_linter: bool = field(default=True)
	linter_lang: str = field(default='en-US')

	linter: RSTLinter | None = field(default=None)

	__custom_dictionary: set[str] = field(default_factory=set)

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
				custom_dictionary=self.__custom_dictionary,
			)
		self.print_errors = self.linter.print_errors

	def add_custom_words(self, *words: str):
		self.__custom_dictionary.update((
			word.strip().lower()
			for word in words
		))

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
		base: Path = Path("source"),
	):
		project_ext = Path("_ext")
		project_ext.mkdir(parents=True, exist_ok=True)
		for _ext_file in _ext_path.glob("*.py"):
			shutil.copy(
				_ext_file,
				project_ext / _ext_file.name
			)
		self.write(
			"title.tex",
			title_template,
			base=base,
			enable_linter=False,
			add_fname_title=False,
		)
		self.write(
			"conf.py",
			config_template.replace(
				'___{extensions}___',
				"\",\n\t\"".join(extensions)
			).replace(
				'___{project}___',
				project
			).replace(
				'___{title}___',
				title
			).replace(
				'___{subtitle}___',
				subtitle
			).replace(
				'___{author}___',
				author
			).replace(
				'___{institution}___',
				institution
			).replace(
				'___{dark}___',
				'True' if dark else 'False'
			),
			base=base,
			enable_linter=False,
			add_fname_title=False,
		)
		if not (base / "definitions.rst").exists():
			self.write("definitions.rst", "", base=base, add_fname_title=False)
		if not (base / "definition_list.rst").exists():
			self.write("definition_list.rst", "", base=base, add_fname_title=False)
		if not (base / "bibliography.bib").exists():
			self.write("bibliography.bib", "", base=base, add_fname_title=False)

	def set_index(
		self,
		*files: Path | str,
		fname: Path | str = "index.rst",
		base: Path = Path("source"),
	):
		self.write(
			fname,
			index_template.format(toctree="\n\t".join(files)),
			base=base,
			enable_linter=False,
			add_fname_title=True,
		)

	def set_bibliography(
		self,
		content: str,
		*,
		fname: Path | str = "bibliography.bib",
		base: Path = Path("source"),
		enable_linter: bool = None,
		style: str = "unsrt",
	):
		self.write(
			"bibliography.rst",
			bibliography_template.format(style=style),
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
		base: Path = Path("source"),
		enable_linter: bool = None,
	):
		self.write(
			"definition_list.rst",
			definition_list_template,
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
		base: Path = Path("source"),
		enable_linter: bool = True,
		enable_syntax_linting: bool = True,
		enable_language_linting: bool = True,
		raise_on_error: bool = False,
		add_fname_title: bool = False,
	):
		if base is not None:
			file = base / file
		elif not isinstance(file, Path):
			file = Path(file)

		file.parent.mkdir(
			parents=True,
			exist_ok=True,
		)

		content = content.strip('\n')

		if file.suffix == '.rst' and add_fname_title:
			content = f"\n{file.stem.upper()}\n{'^' * len(file.stem)}\n\n{content}\n"

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

		with open(file, 'w') as f:
			f.write(content)

		if (enable_linter and enable_syntax_linting and self.linter is not None):
			self.linter.lint_syntax(file)
			if len(self.linter.syntax_errors):
				if raise_on_error:
					self.print_errors()
					raise ValueError("Syntax errors found")
				syn_errors = True

		if syn_errors or lang_errors:
			self.print_errors()

	def build(
		self,
		*,
		source_dir: Path = Path("source"),
		build_dir: Path = Path("build"),
		log_file: Path = Path("build") / "doc.log",
	):
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

		if sphinx_result.returncode != 0:
			print(
				"Error: Sphinx build failed "
				f"(Return code {sphinx_result.returncode}). Aborting."
			)
			if sphinx_result.stderr:
				print("\n[Sphinx STDERR]\n" + sphinx_result.stderr.strip())

			if sphinx_result.stdout:
				print("\n[Sphinx STDOUT]\n" + sphinx_result.stdout.strip())

			class make_result:
				stdout = ''
				stderr = 'Sphinx build failed'
				returncode = 0
		else:
			make_result = subprocess.run(
				['make', '-j', '8'],
				cwd=build_dir,
				capture_output=True,
				text=True,
				check=False
			)

			if make_result.returncode != 0:
				print("\nXXXXXXXXXXXX")
				print(">>> BEGIN DOC.LOG CONTENT (make failed) <<<")
				try:
					with open(log_file, 'r') as f:
						latex_log = f.read()
					print(latex_log)
				except Exception as e:
					print(f"An exceptio occurred: {e}")
				print(">>> END DOC.LOG CONTENT <<<")
			else:
				print("Generated PDF at:", build_dir / "doc.pdf")
				print("Generated LaTeX at:", build_dir / "doc.tex")

	def render_pdf(
		self,
		*,
		build_dir: Path = Path("build"),
		show_page: int | None = None,
	):
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
