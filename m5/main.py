#!/usr/bin/python3

""" Command line API for the m5 package. """

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from textwrap import dedent

from m5.user import User
from m5.settings import show_settings, DEBUG


if __name__ == '__main__':
    """ Command line execution. """

    parser = ArgumentParser(prog='PROG',
                            formatter_class=RawDescriptionHelpFormatter,
                            description=dedent(""" \
        Please do not mess up this text!
         --------------------------------
             I have indented it
             exactly the way
             I want it
         """))

    parser.add_argument('command', metavar='N', type=int, nargs='+',
                  help='an integer for the accumulator')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('download', action='store_true')
    actions.add_argument('migrate', action='store_true')
    parser.add_argument('-s', actions=)
    parser.add_argument('x', type=int, help='the base')
    parser.add_argument('y', type=int, help='the exponent')
    args = parser.parse_args()

    # Just in case

    if DEBUG:
        show_settings()

    u = User()

answer = args.x**args.y

if args.quiet:
    print(answer)
elif args.verbose:
    print('{} to the power {} equals {}'.format(args.x, args.y, answer))
else:
    print('{}^{} == {}'.format(args.x, args.y, answer))

        delta = date.today() - start
    assert isinstance(date, start), 'Please pass a date in the format dd-mm-YY.'
    assert delta >= 0, 'Please pick a date in the past.'
