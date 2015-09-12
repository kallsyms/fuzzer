from random import *
from collections import Counter

# Random mutation

def random_replace(case, n_mutations = 1, rand_range = range(0,255)):
    """Randomly replaces 1 byte in case n_mutations times with a byte in rand_range"""
    
    if max(rand_range) > 255:
        raise ValueError('Maximum of random byte range must be <= 255')
    
    new_case = case
    for i in range(n_mutations):
        position = randrange(len(case))
        new_case = new_case[:position] + chr(choice(rand_range)) + new_case[position+1:]
    
    return new_case


def random_chars(case, n_mutations = 1, chars = ['\x00','\x03','\x04','\x18','\x19','\x1b','\x7f','\r','\n','\'','"','\\']):
    """Identical to random_replace, but with a specific charset by default"""
    
    return random_replace(case, n_mutations, [ord(x) for x in chars])


def random_insert(case, n_mutations = 1, num_insert_range = range(1,10), insert_chars = [chr(x) for x in range(255)]):
    """Randomly inserts num_insert_range bytes within insert_chars n_mutations times into case using"""
    
    new_case = case
    for i in range(n_mutations):
        position = randrange(len(case))
        new_case = new_case[:position] + ''.join(sample(insert_chars, choice(num_insert_range))) + new_case[position:]
    
    return new_case


def random_delete(case, n_mutations = 1, num_delete_range = range(1,10)):
    """Randomly deletes a number of bytes within num_delete_range from c n_mutations times"""
    
    new_case = case
    for i in range(n_mutations):
        position = randrange(len(case) - max(num_delete_range))
        new_case = new_case[:position] + new_case[position+choice(num_delete_range):]
    
    return new_case


# Mutation for human-readable cases

def readable_insert(case, n_mutations = 1):
    """Find common elements in a human-readable case and randomly insert them elsewhere n_mutations times"""
    
    new_case = case
    
    items = new_case.split() # Python auto-splits by spaces, newlines, etc.
    
    if len(items) < 3:
        raise Error('readable_insert should only be used with human-readable cases.')
    
    common = Counter(items).most_common(max(int(len(items)*0.1), 1)) # Get the top 10% most common
    
    for i in range(n_mutations):
        position = randrange(len(case))
        new_case = new_case[:position] + choice(common)[0] + new_case[position:]
    
    return new_case