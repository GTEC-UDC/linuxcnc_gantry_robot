# Author: Tomás Domínguez Bolaño <tomas.bolano@udc.es>
#
# Copyright (c) 2023 Tomás Domínguez Bolaño
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import itertools

from docutils.parsers.rst.directives.images import Image
from sphinx.directives.patches import Figure


sphinx_formats = ['html', 'latex', 'epub', 'texinfo', 'manpage', 'text']
ext_image_options = ['height', 'width', 'scale', 'align', 'class']
ext_figure_options = ext_image_options + ['figwidth', 'figclass']

image_option_spec = Image.option_spec
for opt, f in itertools.product(ext_image_options, sphinx_formats):
    image_option_spec[f'{opt}-{f}'] = image_option_spec[opt]

figure_option_spec = Figure.option_spec
for opt, f in itertools.product(ext_figure_options, sphinx_formats):
    figure_option_spec[f'{opt}-{f}'] = figure_option_spec[opt]


class ExtImage(Image):
    # Extends the default reStructuredText Image directive with
    # the following additional options per format:
    #   - height-<format>: The desired height of the image
    #   - width-<format>: The width of the image
    #   - scale-<format>: The uniform scaling factor of the image
    #   - align-<format>: The alignment of the image
    #   - class-<format>: The class attribute of the image
    #
    # Where <format> may be html, latex, epub, texinfo, manpage, or text
    # When building the documentation for a format, the format specific options
    # will be used if available for Image directive. If the format
    # specific options are not available the corresponding default options
    # will be used instead.

    option_spec = image_option_spec.copy()

    def run(self):
        output_format = self.state.document.settings.env.app.builder.format

        for opt in ext_image_options:
            opt_format = f'{opt}-{output_format}'
            if opt_format in self.options:
                self.options[opt] = self.options[opt_format]

        return super().run()


class ExtFigure(Figure):
    # Extends the default reStructuredText Figure directive with the
    # additional options of ExtImage and also:
    #   - figwidth-<format>: The width of the figure
    #   - figclass-<format>: The class attribute value on the figure element
    #
    # Where <format> may be html, latex, epub, texinfo, manpage, or text
    # When building the documentation for a format, the format specific options
    # will be used if available for Image directive. If the format
    # specific options are not available the corresponding default options
    # will be used instead.

    option_spec = figure_option_spec.copy()

    def run(self):
        output_format = self.state.document.settings.env.app.builder.format

        for opt in ext_figure_options:
            opt_format = f'{opt}-{output_format}'
            if opt_format in self.options:
                self.options[opt] = self.options[opt_format]

        return super().run()


def setup(app):
    app.add_directive('ext-image', ExtImage)
    app.add_directive('ext-figure', ExtFigure)
