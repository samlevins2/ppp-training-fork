#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command Line Interface."""
from argparse import ArgumentParser
from sys import stderr
from copy import copy

from pmix.ppp import run
from pmix.ppp.definitions.constants import SUPPORTED_FORMATS
from pmix.ppp.definitions.abstractions import chain
from pmix.ppp.definitions.error import OdkException, OdkFormError


def _required_fields(parser):
    """Add required fields to parser.

    Args:
        parser (ArgumentParser): Argparse object.

    Returns:
        ArgumentParser: Argeparse object.
    """
    # File
    #   type:'string'
    file_help = 'Path to source XLSForm.'
    parser.add_argument('xlsxfile', help=file_help)
    # Bundled Option Presets
    #   type='single selection', options:'custom, developer, internal,
    #   public', default:'public'
    #   note='the CLI does not have 'custom'. Leaving this option blank in the
    #   CLI os the same as 'custom'.'
    presets_help = \
        ('Select from a preset of bundled options. The \'developer\' preset'
         ' renders a form that is the most similar to the original XlsForm. '
         'The \'internal\' preset is more human readable but is not stripped '
         'of sensitive information. The \'public\' option is like the '
         '\'internal\' optoin, only with sensitive information removed.')
    parser.add_argument('-p', '--preset',
                        choices=('public', 'internal', 'developer', 'minimal'),
                        default='developer', help=presets_help)
    return parser


def _non_preset_optional_fields(parser):
    """Add non-preset optional fields to parser.

    Args:
        parser (ArgumentParser): Argparse object.

    Returns:
        ArgumentParser: Argeparse object.
    """
    # Language
    #   type='single selection', default:''
    language_help = \
        ('Language to write the paper version in. If not specified, the '
         '\'default_language\' in the \'settings\' worksheet is used. If that '
         'is not specified and more than one language is in the XLSForm, the '
         'language that comes first alphabetically will be used.')
    parser.add_argument('-l', '--language', help=language_help)

    # Output Format
    #   type='single selection', default:'html'
    format_help = ('Format to generate. Currently "text" and "html" are '
                   'supported. Future formats include "pdf". If this flag is'
                   ' not supplied, output is html by default.')
    parser.add_argument('-f', '--format',
                        choices=SUPPORTED_FORMATS, default='html',
                        help=format_help)
    return parser


def _preset_optional_fields(parser):
    """Add preset options to parser.

    These options are all boolean toggles. Their value should automatically
    update based on the bundle option preset selected. Also, they should either
    (a) greyed out unless the 'custom bundle option preset is selected, or (b)
    if a bundle option preset other than 'custom' is selected, the bundle
    option preset should automatically change to 'custom' if any of the
    options are changed.


    Args:
        parser (ArgumentParser): Argparse object.

    Returns:
        ArgumentParser: Argeparse object.
    """
    # Input replacement
    #   type='boolean', default:'TRUE if public else FALSE if internal else
    #   FALSE if developer'
    input_replacement_help = \
        ('Adding this option will toggle replacement of visible choice '
         'options in input fields. Instead of the normal choice options, '
         'whatever has been placed in the \'ppp_input\' field of the XlsForm '
         'will be used. This is normally to hide sensitive information.')
    parser.add_argument('-i', '--input-replacement', action='store_true',
                        help=input_replacement_help)

    # Exclusion
    #   type='boolean', default:'TRUE if public else FALSE if internal else
    #   FALSE if developer
    exclusion_help = \
        ('Adding this option will toggle exclusion of certain survey form '
         'compoments from the rendered form. This can be used to remove '
         'ODK-specific implementation elements from the form which are only '
         'useful for developers, and can also be used to wholly remove '
         'sensitive information without any replacement.')
    parser.add_argument('-e', '--exclusion', action='store_true',
                        help=exclusion_help)

    # Human-readable relevant text
    #   type='boolean', default:'TRUE if public else TRUE if internal else
    #   FALSE if developer
    hr_relevant_help = \
        ('Adding this option will toggle display of human readable '
         '\'relevant\' text, rather than the syntax-heavy codified logic of '
         'the original XlsForm.')
    parser.add_argument('-r', '--hr-relevant', action='store_true',
                        help=hr_relevant_help)

    # Human-readable constraint text
    #   type='boolean', default:'TRUE if public else FALSE if internal else
    #   FALSE if developer
    hr_constraint_help = \
        ('Adding this option will toggle display of human readable '
         '\'constraint\' text, rather than the syntax-heavy codified logic of '
         'the original XlsForm.')
    parser.add_argument('-c', '--hr-constraint', action='store_true',
                        help=hr_constraint_help)

    # No constraint text
    #   type='boolean', default:'FALSE if public else FALSE if internal
    #   else FALSE if developer
    no_constraint_help = \
        ('Adding this option will toggle removal of all constraints from the '
         'rendered form.')
    parser.add_argument('-C', '--no-constraint', action='store_true',
                        help=no_constraint_help)

    # General text replacements
    #   type='boolean', default:'TRUE if public else TRUE if internal else
    #   FALSE if developer
    text_replacements_help = \
        ('Adding this option will toggle text replacements as shown in the '
         '\'text_replacements\' worksheet of the XlsForm. The most common '
         'function of text replacement is to render more human readable '
         'variable names, but can also be used to remove sensitive information'
         'or add brevity or clarity where needed.')
    parser.add_argument('-t', '--text-replacements', action='store_true',
                        help=text_replacements_help)
    return parser


def _cli_only_fields(parser):
    """Add CLI-only fields to parser.

    Args:
        parser (ArgumentParser): Argparse object.

    Returns:
        ArgumentParser: Argeparse object.
    """
    # Debug
    debug_help = \
        'Turns on debug mode. Currently only works for \'html\' format. Only' \
        ' feature of debug mode currently is that it prints a stringified ' \
        'JSON representation of survey to the JavaScript console.'
    parser.add_argument('-d', '--debug', action='store_true', help=debug_help)

    # Survey Form Component Highlighting
    highlighting_help = 'Turns on highlighting of various portions of survey' \
                        ' components. Useful to assess positioning.'
    parser.add_argument('-H', '--highlight', action='store_true',
                        help=highlighting_help)

    # Out path
    out_help = ('Path to write output. If this argument is not supplied, then '
                'STDOUT is used.')
    parser.add_argument('-o', '--outpath', help=out_help)
    return parser


def _add_arguments(parser):
    """Add arguments to parser.

    Args:
        parser (ArgumentParser): Argparse object.

    Returns:
        ArgumentParser: Argeparse object.
    """
    return chain(parser, funcs=[_cli_only_fields, _non_preset_optional_fields,
                                _preset_optional_fields, _required_fields])


def cli():
    """Command line interface for package.

    Side Effects: Executes program.

    Command Syntax: python3 -m pmix.ppp <file> <options>

    Examples:
        # Creates a 'myFile.html' in English with component highlighting.
        python3 -m pmix.ppp myFile.xlsx -l 'English' -h > myFile.html
    """
    prog_desc = 'Convert XLSForm to Paper version.'

    argeparser = ArgumentParser(description=prog_desc)
    parser = _add_arguments(copy(argeparser))
    args = parser.parse_args()

    if args.highlight and args.format and args.format not in SUPPORTED_FORMATS:
        msg = 'Can only specify highlighting when using the following ' \
              'formats: \'html\', \'pdf\'.'
        raise OdkFormError(msg)

    try:
        run(in_file=args.xlsxfile, language=args.language,
            output_format=args.format, out_file=args.outpath,
            debug=args.debug, highlight=args.highlight, preset=args.preset)
    except OdkException as err:
        err = 'An error occurred while attempting to convert \'{}\':\n{}'\
            .format(args.xlsxfile, err)
        print(err, file=stderr)


if __name__ == '__main__':
    cli()