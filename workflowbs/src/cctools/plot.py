# Copyright (c) 2011- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

""" CCTools Plotting module """




import os

__all__ = ['gnuplot', 'GNUPlotField']


# GNU Plot

#: List of recognized GNU Plot formats.
GNUPLOT_FORMATS = {
    'eps':  'postscript enhanced color eps 24',
    'png':  'png 24',
}

#: List of recognized GNU Plot string fields.
GNUPLOT_STRING_FIELDS = [
    'xlabel', 'ylabel', 'format x', 'format y', 'title', 'timefmt',
]


class GNUPlotField(object):
    """ This is a specification of the GNU Plot field.

    :param title:       Field title.
    :param columns:     Columns from data file to select.
    :param type:        Line type.
    :param datapath:    Path to custom data file.
    :param style:       Line style.

    If `type` is not specified then it is set to "lines".

    If `datapath` is not specified then the `data_path` passed to
    :func:`gnuplot` is utilized.
    """
    def __init__(self, title, columns, type=None, data_path=None, style=None):
        self.title     = title
        self.columns   = columns
        self.type      = type or 'lines'
        self.data_path = data_path
        self.style     = style


def gnuplot(plot_path, data_path, plot_format=None, plot_fields=None, **kwargs):
    """ Generate gnuplot using specified data file and configuration.

    :param plot_path:   Plot file to generate (usually an image).
    :param data_path:   Path to data file to use.
    :param plot_format: Plot format (eps, png).
    :param plot_fields: Fields to plot.

    Additional keyword arguments are recognized as parameters to GNUPlot.
    """
    script_path = os.path.splitext(plot_path)[0] + '.gnuplot'

    with open(script_path, 'w+') as fs:
        print('set output "{0}"'.format(plot_path), file=fs)
        for key, value in list(kwargs.items()):
            if key in GNUPLOT_STRING_FIELDS:
                print('set {0} "{1}"'.format(key, value), file=fs)
            else:
                print('set {0} {1}'.format(key, value), file=fs)

        if plot_format:
            try:
                terminal_setting = GNUPLOT_FORMATS[plot_format]
                print('set terminal {0}'.format(terminal_setting), file=fs)
            except KeyError:
                pass # TODO: warning

        if plot_fields is None:
            plot_fields = []

        field_strings = []
        for i, field in enumerate(plot_fields):
            if field.data_path is None:
                field.data_path = data_path
            if field.style is None:
                if field.type == 'lines':
                    field.style = 'lt {0} lw 5'.format(i + 1)
                else:
                    field.style = ''

            field_strings.append(
                '"{0}" using {1} title "{2}" with {3} {4}'.format(
                    field.data_path, field.columns, field.title, field.type, field.style))

        print('plot', ', '.join(field_strings), file=fs)

    return os.system('gnuplot < {0}'.format(script_path))

# vim: set sts=4 sw=4 ts=8 expandtab ft=python:
