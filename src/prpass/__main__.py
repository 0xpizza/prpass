#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# put some license info here or something


if __name__ == '__main__':
    import argparse
    from .passwordgenerator import PasswordGenerator
    parser = argparse.ArgumentParser(description='Pseudorandom password generator.')
    parser.add_argument('-g', '--gui', action='store_true', help='Start the graphical user interface.')
    parser = parser.parse_args()
    
    if parser.gui:
        from . import gui
        gui.run()
    else:
        from . import cli
        cli.run()
        
