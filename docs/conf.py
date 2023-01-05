# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import django

from django.conf import settings

sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('../sortinghat'))

settings.configure(
    SECRET_KEY = 'fake_key',
    INSTALLED_APPS=[
        'sortinghat.core',
        'django.contrib.contenttypes',
        'django.contrib.admin',
        'django.contrib.auth'
    ],
    RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'ASYNC': True,
        'DB': 0
        }
    },
    DEFAULT_GRAPHQL_PAGE_SIZE = 2
)
django.setup()
os.system("sphinx-apidoc -f -o source/ ../")


# -- Project information -----------------------------------------------------

project = 'SortingHat'
copyright = '2021, GrimoireLab'
author = 'GrimoireLab Developers'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    'myst_parser',
]

source_suffix = ['.rst', '.md']
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**tests**']

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "light_css_variables": {
        "font-stack": "system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica Neue,Arial,sans-serif",
        "font-stack--monospace": "Courier, monospace",
    },
}

html_title = "SortingHat Docs"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

autodoc_mock_imports = ["settings"]
