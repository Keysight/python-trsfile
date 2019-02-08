import setuptools
import trsfile

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name                          = trsfile.__name__,
	version                       = trsfile.__version__,
	author                        = trsfile.__author__,
	author_email                  = trsfile.__contact__,
	description                   = (
		"Library to read and create Riscure Inspector trace set files (.trs)"
	),
	long_description              = long_description,
	long_description_content_type = "text/markdown",
	url                           = "https://github.com/riscure/python-trsfile",
	packages                      = setuptools.find_packages(),
	install_requires              = [
		'numpy',
	],
	license                       = "BSD 3-Clause Clear License",
	keywords                      = "trs trace inspector riscure",
	classifiers                   = [
		"Development Status :: 4 - Beta",
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: BSD License",
		"Topic :: Utilities",
		"Operating System :: OS Independent",
	],
	project_urls                  = {
		'Documentation': 'https://trsfile.readthedocs.io/en/latest',
		'Bug Reports'  : 'https://github.com/riscure/python-trsfile/issues',
		'Riscure'      : 'https://www.riscure.com',
	},
	# entry_points                  = {
	# 	'console_scripts': [
	# 		"trsfile = trsfile.cli:main",
	# 	]
	# },
)
