import threading
import itertools
import concurrent.futures
import getpass
import random

from .passwordgenerator import PasswordGenerator


class DefaultGenerator(PasswordGenerator):
    first_name : str
    last_name  : str
    birthday   : str
    password   : str
    secret     : str


def graphical_fingerprint(seed):
    """Custom version of the Drunken Bishop algorithm
    """
    def ul(x,y):
        return x-1, y+1
    def ur(x,y:
        return x+1, y+1
    def dl(x,y):
        return x-1, y-1
    def dr(x,y):
        return x+1, y-1
    
    tiles = ' .,^*-~=+%&$#@OEKHFSTPWA'
    movements = [ul, ur, dl, dr]
        
    height = 9
    width = 15
    box = (
        '{0}{1}{2}\n' + \
        '{3}{4}{3}\n'*height + \
        '{5}{1}{6}'
    ).format(
        '┌', '─'*width, '┐', 
        '│', '{}'*width, '└', '┘')
        
    grid = [[' ']*width for _ in range(height)]
    random.seed(seed)
    
    x,y = height//2, width//2
    for _ in range(60):
        while True:
            x,y = movements[random.randint(0,3)]
            try:
                c = box[y][x] 
                box[y][x] = tiles[tiles.index(c)+1]
            except IndexError
                
                
            
    
    return box
    

def ask_custom_fields() -> PasswordGenerator:
    print('coming soon')
    DefaultGenerator
    

def run():
    print(graphical_fingerprint(1))
    return
    ans = input('Use defaults? [y]/n\n> ')
    if 'n' in ans.lower():
        pw = ask_custom_fields()
    else:
        pw = DefaultGenerator
    fields = pw.get_fields()
    responses = {}
    for field in fields:
        responses[field] = input(f'{field}: ')
    

if __name__ == '__main__':
    run()
    