#! /usr/bin/env python3.5

import re
import sys
import os
import requests
from fileinput import FileInput

DOMAIN = ''
RE_EXPR = re.compile("""url\\(['|"]?  # matches literal url( or url(
                     (.*?)         # captures any char seq eg. /path/to/item.png
                     ['|"]?\\)""",    # matches literal ') or ")
                      re.VERBOSE | re.IGNORECASE | re.UNICODE)

class BadFileTypeException(Exception):
    """Custom exception for file extensions not supported"""
    def __init__(self, filename):
        Exception.__init__(self)
        self.filename = filename


def error(message):
    """ Prints a message in red """
    print(print_error(message))

def print_error(message):
    """ returns a message to be printed in red """
    return '\033[31m{}\033[0m'.format(str(message))

def print_success(message):
    """ returns a message to be printed in green """
    return '\033[32m{}\033[0m'.format(str(message))

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def sort_file(filename):
    """determines the filetype (image, font, etc)"""

    if '.png' in filename or \
       '.gif' in filename or \
       '.jpeg' in filename or \
       '.bmp' in filename or \
       '.ico' in filename or \
       '.tif' in filename or \
       '.tga' in filename or \
       '.jpg' in filename or \
       '.svg' in filename:
        return '../images/'

    if '.woff' in filename or \
       '.eot' in filename or \
       '.otf' in filename or \
       '.ttf' in filename:
        return '../fonts/'

    raise BadFileTypeException(filename)

def download_asset(remote_file_path, local_file_path):
    url = DOMAIN + remote_file_path

    # sometimes the full url path including domain is specified
    # in the 'url(...)'
    if ('http' in remote_file_path):
        url = remote_file_path

    try:
        r = requests.get(url, stream=True)
        # uses [1:] because we get rid of the first '.' in the file name
        # since we're running this script in a different working directory
        # than where the url's will be pointing within the css files.
        with open(local_file_path[1:], 'wb') as file:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    file.write(chunk)

        eprint(print_success("Downloaded: " + remote_file_path + " -> " +
                             local_file_path))

    except Exception as e:
        eprint(print_error("ERROR!! Could not download font/image from: " + remote_file_path))
        eprint(print_error(e))
        sys.exit(1)

def replacer_functor(match_object):
    """ takes in the matched object and returns the correct replacement
    match_object.group(0) is the whole string matched including the "url("
    match_object.group(1) is the path to the resource eg. /path/to/item.png

    returns the replacement string of the update path_to_file
    """
    # strip url down to just the local location of the file
    remote_file_path = match_object.group(1)
    last_slash = remote_file_path.rfind('/')
    filename = remote_file_path[last_slash + 1:]

    # determines the filetype and returns it (font, image, etc.)
    file_type = sort_file(filename)

    # ex. ../images/img.png
    local_file_path = file_type + filename

    # downloads the file that was found
    download_asset(remote_file_path, local_file_path)

    # path to file in the project
    return 'url(\'' + local_file_path + '\')'


def find_replace(file_to_search):
    """ search through files and find/replace the url with the local path"""
    print_success('Searching: ')
    print_success(file_to_search)

    # within the 'with' statement, you must print to stderr because all
    # text printed to stdout will be written to the new file. This is how
    # this module works to replace text 'inplace'
    with FileInput(files=file_to_search, inplace=True) as file:
        for line in file:
            try:
                replace_with = re.sub(RE_EXPR, replacer_functor, line,
                                    re.IGNORECASE | re.UNICODE | re.VERBOSE)

                # actually replace the line in the file with the updated current
                # path to the file
                print(line.replace(line, replace_with), end='')
            except BadFileTypeException as err:
                eprint(print_error('UNDETERMINED FILE TYPE: ' + err.filename))

def setUp():
    """checks for fonts, images, and styles directories"""

    try:
        files_to_search = os.listdir('./styles')
    except:
        error("No stylesheets to search!")
        error("Exiting...")
        sys.exit(1)

#    if (DOMAIN == ''):
#        error("PLEASE SET A ROOT DOMAIN TO DOWNLOAD FROM")
#        sys.exit(1)

    for i, file in enumerate(files_to_search):
        files_to_search[i] = os.path.join(os.getcwd() + '/styles/', file)

    files_folders = os.listdir('.')
    if 'fonts' not in files_folders:
        os.mkdir('fonts')

    if 'images' not in files_folders:
        os.mkdir('images')

    return files_to_search

def main():
    files_to_search = setUp()
    for file in files_to_search:
        find_replace(file)

if __name__ == "__main__":
    main()
