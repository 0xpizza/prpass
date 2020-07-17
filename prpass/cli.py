
# -*- coding: utf-8 -*-

import os
import sys
import random
import getpass
import threading
import itertools
import concurrent.futures

from .passwordgenerator import PasswordGenerator


class ReasonableDefault(PasswordGenerator):
    full_name     : str
    birthday      : str
    password      : str
    miscellaneous : str = ''  # miscellaneous field for whatever


def text_fingerprint(seed):
    """Custom version of the Drunken Bishop algorithm based
    on Mersenne Twister algorithm instead of bit interpretation.
    
    This function will 
    """
    
    # prng
    random.seed(seed)

    rounds = 72
    height = 9
    width  = 17
    # TODO: make I symbols purple to contain the secrets of life and death
    tiles  = ' ~+=*oI0@OWMPSKLPA'  
    movements = [
        lambda x,y: (x-1, y+1),
        lambda x,y: (x+1, y+1),
        lambda x,y: (x-1, y-1),
        lambda x,y: (x+1, y-1),
    ]
    
    # build a format string
    artwork = (
        '{0}{1}{2}\n' + \
        '{3}{4}{3}\n'*height + \
        '{5}{1}{6}'
    ).format(
        '┌', '─'*width, '┐', 
        '│', '{}'*width, '└', '┘')
        
    # set up the art we will plug into the frame
    grid = [[' ']*width for _ in range(height)]
    
    x,y = height//2, width//2
    for _ in range(rounds):
        
        x,y = movements[random.randint(0,3)](x,y)            
        
        if x > width-1:
            x -= 1
        if x < 0:
            x += 1
        
        if y > height-1:
            y -= 1
        if y < 0:
            y += 1
        
        i = tiles.index(grid[y][x])+1
        if i >= len(tiles):
            # too many rounds, or a sadly idle bishop will exhaust the 
            # allowed character pool! Compensate with overflow character
            t = '?'  
        else:
            t = tiles[i]
        grid[y][x] = t

    # fill format string in with our grid
    c = itertools.chain
    return artwork.format(*c(*c(grid)))
        
    
def input(s):
    try:
        return __builtins__.get('input')(s)
    except (KeyboardInterrupt, EOFError):
        raise SystemExit


def ask_custom_fields() -> PasswordGenerator:
    while True:
        fields = input('Enter all desired field names separated by spaces:\n')
        try:
            assert all(c.isalnum() or c in '_ '  for c in fields)
            assert not fields[0].isnumeric()
            return PasswordGenerator.new(fields.split())
        except:
            print('Invalid field names. Field names cannot start with a number, and can only contain letters, numbers, and underscores.')
            
    
def clear_screen():
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')
    
    
    
def ask_yes_no(s, default='y'):
    if default == 'y':
        dstr = f'[y]/n'
    else:
        dstr = f'y/[n]'
        
    prompt = f'{s} ({dstr})?'
    while True:
        r = input(prompt).lower().strip()
        if not r:
            if default == 'y':
                return True
            else:
                return False
        if 'y' in r:
            if 'n' in r:
                print('Please respond with yes or no.')
                continue
            return True
        elif 'n' in r:
            return False
        else:
            print('Please respond with yes or no.')
    


def ask_choice(options):
    while True:
        print('Which would you like?')
        for i, v in enumerate(options):
            print(f'{i+1}) {v}')
        i = input(' > ')
        try:
            return options[int(i)-1]
        except:
            print('Invalid selection.')


def run():
    if ask_yes_no('Use defaults?'):
        pw_gen = ReasonableDefault
        hash_algorithm = None  # pw_gen will pick the best one.
    else:
        if ask_yes_no('Would you like to use custom fields?', default='n'):
            pw_gen = ask_custom_fields()
        else:
            pw_gen = ReasonableDefault
            
        if ask_yes_no('Would you like to change algorithms?', default='n'):
            hash_algorithm = ask_choice(pw_gen.get_available_algorithms())
    
    fields = pw_gen.get_fields()
    
    responses = {}
    
    # Setup the generator
    while True:
        for field in fields:
            responses[field] = input(f'{field.title()}: ')
            clear_screen()
        
        pw = pw_gen(**responses)
        
        if hash_algorithm:
            pw.set_algorithm(hash_algorithm)
            
        clear_screen()
        
        print('\n\nUsing algorithm:', pw.get_hash_name())
        print('Deriving key...', end=' ')
        fingerprint = pw.derive_key()
        print('Done.')
        
        print('Your key looks like this:')
        print(text_fingerprint(fingerprint))
        print(f'({fingerprint.hex()})')
        if ask_yes_no('\nIs this correct'):
            break
        
        if ask_yes_no('Would you like to change algorithms?', default='n'):
            hash_algorithm = ask_choice(pw.get_available_algorithms())
            
        
    # Generate some passwords!
    while True:
        service_name = input('What would you like the password for?\n> ')
        print(pw.get_password(service_name))
        input('Press Enter to continue...')
        clear_screen()
    

if __name__ == '__main__':
    run()















