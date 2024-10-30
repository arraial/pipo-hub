# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pipo_hub"
copyright = "2024, Tiago Gonçalves"
author = "Tiago Gonçalves, André Gonçalves, Miguel Peixoto"

version = release = "0.1.0"

nitpicky = True

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "autoapi.extension",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.githubpages",
    "sphinx_immaterial",
]

master_doc = "index"
templates_path = ["_templates"]
exclude_patterns = ["_build", "_templates"]
show_authors = True
add_function_parentheses = False
language = "en"

# -- Options for autoapi ----------------------------------------------
autoapi_dirs = ["../pipo_hub"]

# -- Options for napoleon ----------------------------------------------
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = False
napoleon_preprocess_types = True
napoleon_attr_annotations = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_immaterial"
html_extra_path = []
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/sinistro14/pipo/",
    "source_branch": "main",
    "source_directory": "docs/",
}
html_baseurl = "https://arraial.github.io/pipo_hub"

# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration
todo_include_todos = True
