"""
Various utilities that may come handy for the plugins.
"""

import io
import os


def reversed_lines(file_or_path, encoding='utf-8'):
    """Generate the lines of file in reverse order.

    :param file_or_path: Either
    :type file_or_path: file | basestring
    :param str encoding: Encoding of the strings read from the file.

    :return: Lines from the file in reversed order.
    :rtype: list of unicode
    """
    part = ''
    with io.open(file_or_path, encoding=encoding) as file:
        for block in reversed_blocks(file):
            for c in reversed(block):
                if c == '\n' and part:
                    yield part[::-1]
                    part = ''
                part += c
        if part:
            yield part[::-1]


def reversed_blocks(file, blocksize=io.DEFAULT_BUFFER_SIZE):
    """Generate blocks of file's contents in reverse order.

    :param io.TextIOBase file: The file to read blocks from.
    :param int blocksize: Size of the reading buffer.

    :return: Blocks of size blocksize.
    :rtype: list of unicode
    """
    file.seek(0, os.SEEK_END)
    here = file.tell()
    while 0 < here:
        delta = min(blocksize, here)
        here -= delta
        file.seek(here, os.SEEK_SET)
        yield file.read(delta)
