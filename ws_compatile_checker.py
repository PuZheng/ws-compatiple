#! /usr/bin/env python
# -*- coding: UTF-8 -*-
'''
USAGE:
    ws_compatiple_checker.py <url1> <url2>

SYNOPSIS:
    is url2 compatiple with url1? note, both in JSON format, all string should
    UTF-8 encoded.
    NOTE!!! COMPABILITY is a complex thing, the COMPABILITY here means:

    if url1 returns a list (or any lists included in response), say L1,
    then url2 should still returns a list, say L2, and:

    1. if all elements in L1, L2 are of the same SCALAR type. each element in
    L1, L2 should be of same type, no matter the length of L1, L2, eg.
    "[1, 2, 3]" if compatiple with "[1, 2]"
    2. if all elements in L1, L2 are of the same NON-SCALAR type, each element
    in L1, L2 should be of the same type, no matter the lenght of L1, L2, and
    the each element in L1 is checked against L2. eg.
    "[{'a': 1, 'b': 2}, {'a': 1, 'b': 2}]" is compatiple with
    "[{'a': 1, 'b': 2}, {'a': 1, 'b': 2}, {'a': 1, 'c': 2}]", of course, you
    may think this is a little bizzare, but I think this is your design flaw.
    3. if all elements in L1, L2 are not of the same type. then, length of L1,
    L2 must be the same, and each element is checked, eg. "[1, 's', {'x': 1}]"
    if NOT compatiple with "[1, 2, 3]".
    4. empty list is not compatiple with non empty list, and vice versa

    if url1 returns a dict, say D1, and url2 should still returns a dict, say
    D2, and:

    1. all the keys in D1 should be in D2, NOTE, not vice versa.
    2. D1[key] is checked against D2[key] for each key in D1


    IN A WORD, these API design principles are strongly encouraged:

    1. all elements in a list are of the same type and INDEPENDENT entites.
    2. if a field is null, still returns the default value. don't let the caller
        make judgement.
    3. a list/entity has only one canonical representation
    4. use dict to represent object/entity, list to represent a list of objects
'''
import sys
import json
import collections
import requests
import pprint


def is_scalar(value):
    return isinstance(value, (type(None), str, int, float, bool, unicode))


class Incompatiple(Exception):

    def __init__(self, context, msg, data1, data2):
        super(Incompatiple, self).__init__(self, msg)
        self.context = context
        self.msg = msg
        self.data1 = data1
        self.data2 = data2

    def pprint(self):
        print ("CONTEXT: %s " % self.context) + self.msg.upper()
        pprint.pprint('======================================================')
        pprint.pprint(data1)
        pprint.pprint('======================================================')
        pprint.pprint(data2)


def compatiple(context, data1, data2):
    '''
    >>> compatiple('root', 's1', 's2')
    >>> compatiple('root', '1', 1)
    Traceback (most recent call last):
        ...
    Incompatiple: (Incompatiple(...), 'type incompatiple')
    >>> compatiple('root', {'a': 1}, {'a': 1, 'b': 2})
    >>> compatiple('root', {'a': 1}, {'a': '1', 'b': 2})
    Traceback (most recent call last):
        ...
    Incompatiple: (Incompatiple(...), 'type incompatiple')
    >>> compatiple('root', {'c': 1}, {'a': '1', 'b': 2})
    Traceback (most recent call last):
        ...
    Incompatiple: (Incompatiple(...), 'no such key')
    >>> compatiple('root', [1, 2, 3], [4, 5, 6, 7])
    >>> compatiple('root', [1, 2, 3], [4, 5, 6, 's'])
    Traceback (most recent call last):
        ...
    Incompatiple: (Incompatiple(...), 'type incompatiple')
    >>> compatiple('root', [{'a': 1, 'b': 2}, {'c': 1, 'd': 2}], \
[{'a': 1, 'b': 2}, {'c': 1, 'd': 2}, {'e': 1, 'f': 2}])
    >>> compatiple('root', [], [1])
    Traceback (most recent call last):
        ...
    Incompatiple: (Incompatiple(...), 'empty list')
    >>> compatiple('root', [1], [])
    Traceback (most recent call last):
        ...
    Incompatiple: (Incompatiple(...), 'empty list')
    >>> compatiple('root', {'a': [1, 2, 3], 'b': {'x': 1, 'y': 2}, 'c': 1}, \
{'a': [1, 2, 3, 4, 5], 'b': {'x': 1, 'y': 10, 'z': 20}, 'c': 0, 'd': 'lkj'})
    '''
    if is_scalar(data1):
        if type(data1) == type(data2):
            return
        raise Incompatiple(context, 'type incompatiple', data1, data2)
    if isinstance(data1, dict):
        if not isinstance(data2, dict):
            raise Incompatiple(context, 'type incompatiple', data1, data2)
        for key in data1:
            if key not in data2:
                raise Incompatiple(key, 'no such key', data1, data2)
            compatiple(key, data1[key], data2[key])
    if isinstance(data1, collections.Sequence):
        if len(data1) == 0 or len(data2) == 0:
            if len(data1) != len(data2):
                raise Incompatiple(context, 'empty list', data1, data2)
        if all([type(x) == type(data1[0]) for x in data1]):
            for i in data2:
                if type(i) != type(data1[0]):
                    raise Incompatiple(context, 'type incompatiple', i,
                                       data1[0])
            if is_scalar(data1[0]):
                return
            else:
                for x, y in zip(data1, data2):
                    compatiple(context, x, y)
        else:
            if len(data1) != len(data2):
                raise Incompatiple(context, 'length not equal', data1, data2)
            for x, y in zip(data1, data2):
                compatiple(context, x, y)

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print __doc__
        sys.exit(1)

    url1 = sys.argv[1]
    url2 = sys.argv[2]
    data1 = json.loads(requests.get(url1).text)
    data2 = json.loads(requests.get(url2).text)

    try:
        compatiple('root', data1, data2)
    except Incompatiple, e:
        e.pprint()
