# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import re
import sys
import textwrap
from sphinx.highlighting import lexers

# extend system path
sys.path.append(os.path.abspath("_extensions"))
sys.path.append(os.path.abspath("_pygments"))

from hal_lexer import HALLexer


# register hal lexer
lexers["hal"] = HALLexer()


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "LinuxCNC Gantry Robot System"
author = "Tomás Domínguez Bolaño, Valentín Barral Vales, Carlos José Escudero Cascón, and José Antonio García Naya"
copyright = "%Y, Tomás Domínguez Bolaño, Valentín Barral Vales, Carlos José Escudero Cascón, and José Antonio García Naya (CITIC Research Center, University of A Coruña, Spain)"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinxcontrib.bibtex",  # https://github.com/mcmtroffaes/sphinxcontrib-bibtex
    "sphinx_copybutton",  # https://github.com/executablebooks/sphinx-copybutton
    "extimage",  # Provides ext-image and ext-figure directives
    "myst_parser",  # https://myst-parser.readthedocs.io/en/latest/
]

bibtex_bibfiles = ["bib/references.bib"]
bibtex_default_style = "unsrtalpha"

# pygments_style = "manni"
# pygments_dark_style = "monokai"

templates_path = ["_templates"]
# exclude_patterns = []

myst_enable_extensions = [
    "amsmath",
    "attrs_inline",
    "colon_fence",
    "dollarmath",
    "replacements",
    "substitution",
]

myst_substitutions = {"project": project}

numfig = True
numfig_secnum_depth = 0
math_numfig = True
highlight_language = "none"

numfig_format = {
    "code-block": "Código %s",
    # 'figure': 'Figura %s',
    # 'section': 'Sección',
    # 'table': 'Tabla %s',
}

# Define acronyms. These will be added to rst_prolog using the abbr directive
acronyms = {
    "ACPI": "Advanced Configuration and Power Interface",
    "APM": "Advanced Power Management",
    "BIOS": "Basic Input/Output System",
    "CNC": "control numérico computerizado",
    "CPU": "central processing unit",
    "DRO": "Digital Read Out",
    "EE.UU.": "Estados Unidos de América",
    "EIA": "Electronic Industries Alliance",
    "EMC": "Enhanced Machine Controller",
    "EMC2": "Enhanced Machine Controller 2",
    "GPL": "GNU General Public License",
    "GUI": "graphical user interface",
    "HAL": "Hardware Abstraction Layer",
    "LGPL": "GNU Lesser General Public License",
    "MDI": "manual data input",
    "NAMES": "North American Model Engineering Society",
    "NIST": "National Institute of Standards and Technology",
    "NML": "Neutral Message Language",
    "P": "proporcional",
    "PI": "proporcional e integral",
    "PID": "proporcional, integral, y derivativo",
    "PLC": "programmable logic controller",
    "PMAC": "programmable multi-axis controller",
    "PPR": "pulsos por revolución",
    "RCU": "Read-Copy-Update",
    "SMI": "System Management Interrupt",
    "UEFI": "Unified Extensible Firmware Interface",
}

for acronym, text in acronyms.items():
    myst_substitutions[acronym] = f"{{abbr}}`{acronym} ({text})`"


# -- Options for internationalization ----------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-internationalization

language = "es"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"

html_title = project

html_theme_options = {
    # furo theme options
    # "source_repository": "https://github.com/...",
    # "source_branch": "master",
    # "source_directory": "/",
    "light_css_variables": {
        # inherited by the dark mode
        "font-stack": "IBM Plex Sans, Helvetica, sans-serif",
        "font-stack--monospace": "IBM Plex Mono, monospace",
    },
}

html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "css/custom.css",
    # "css/furo_custom.css",
    # "css/sphynx_copybutton.css",
    "css/tables.css",
]

html_logo = "images/logos/logo_udc_gtec_citic.svg"
html_favicon = "images/favicon.png"
html_last_updated_fmt = "%b %d, %Y"
html_show_copyright = True
html_show_sphinx = True

# -- Options for LaTeX output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-latex-output

latex_engine = "lualatex"
latex_show_urls = "no"
latex_table_style = ["booktabs"]

latex_logo = "images/logos/logo_udc_gtec_citic.pdf"

latex_documents = [
    (
        "index",
        "linuxcncgantryrobot.tex",
        project,
        "Tomás Domínguez Bolaño \\and Valentín Barral Vales \\and Carlos José Escudero Cascón \\and José Antonio García Naya",
        "manual",
    )
]

# Additional documents to include
latex_additional_files = [
    "latex/preamble.sty",
    "latex/endofbody.sty",
]

# Document main settings
latex_elements = {
    "atendofbody": r"\input{endofbody.sty}",
    "extrapackages": textwrap.dedent(
        r"""
        \usepackage{fontspec}
        \usepackage{microtype}
        \usepackage{ragged2e}
        \usepackage{newunicodechar}
        """
    ),
    "extraclassoptions": "openany",
    "figure_align": "!ht",
    "fncychap": r"\usepackage[Lenny]{fncychap}",
    "fontpkg": textwrap.dedent(
        r"""
        \usepackage[
            usefilenames,
            RMstyle={Text,Semibold},
            SSstyle={Text,Semibold},
            TTstyle={Text},
            DefaultFeatures={Ligatures=Common}
        ]{plex-otf} %
        """
    ),
    # "fontpkg": textwrap.dedent(
    #     r"""
    #     \usepackage{plex-serif}
    #     \usepackage{plex-sans}
    #     \usepackage{plex-mono}
    #     \renewcommand*\familydefault{\sfdefault}
    #     """
    # ),
    "fvset": textwrap.dedent(
        r"""\fvset{
        fontsize=\footnotesize,
        % numbers=left,
        numbersep=8pt
        }
        """
    ),
    "papersize": "a4paper",
    "passoptionstopackages": textwrap.dedent(
        r"""
        \PassOptionsToPackage{svgnames}{xcolor}
        """
    ),
    "pointsize": "11pt",
    "preamble": r"\input{preamble.sty}"
    + "\n"
    + r"\authoraddress{CITIC Research Center, University of A Coruña, Spain}",
    "sphinxsetup": textwrap.dedent(
        r"""
        hmargin=115pt,
        vmargin={100pt,100pt},
        verbatimvisiblespace=\textcolor{red}{\fontfamily{cmr}\selectfont\textvisiblespace},
        verbatimwithframe=false,
        pre_border-radius=0pt,
        """,
    ),
}

# Admonitions to configure
admonitions = [
    "note",
    "hint",
    "important",
    "tip",
    "warning",
    "caution",
    "attention",
    "danger",
    "error",
]

# if there is not a coma at the end of sphinxsetup add one
if re.match(r",\s+$", e := latex_elements["sphinxsetup"]) is None:
    latex_elements["sphinxsetup"] = re.sub(r",\s+$", ",\n", e)

# Add admonition settings to sphinxsetup
for adm in admonitions:
    latex_elements["sphinxsetup"] += (
        rf"div.{adm}_border-TeXcolor=DarkGray," + "\n"
        rf"div.{adm}_TeXextras=\small," + "\n"
        rf"div.{adm}_box-decoration-break=slice," + "\n"
    )
