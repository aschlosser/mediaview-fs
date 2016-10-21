#!/usr/bin/env python3

import os, os.path
from xml.dom.minidom import parse
from collections import defaultdict

MEDIA_TYPES = {'tvshow':'TV Shows','movie':'Movies'}

class Media:
    def __init__(self, nfo_path):
        self.base = os.path.dirname(nfo_path)
        dom = parse(nfo_path)
        root = (dom.getElementsByTagName('movie') + dom.getElementsByTagName('tvshow'))[0]
        self.type = MEDIA_TYPES[root.tagName]
        self.tags = {}
        self.title = root.getElementsByTagName('title')[0].firstChild.nodeValue
        self.tags['Genre'] = list(map(lambda x: x.firstChild.nodeValue, root.getElementsByTagName('genre')))


def recursive_media_search(rootdir):
    for root, _, files in os.walk(rootdir, topdown=False):
        for file in files:
            if file.endswith('.nfo'):
                try:
                    m = Media(os.path.join(root, file))
                    yield m
                except:
                    pass


def build_virtual_paths(rootdir):
    allpath = '/{mediatype}/byTitle/{title}'
    path = '/{mediatype}/by{tagname}/{tagvalue}/{title}'
    vpaths = {}
    vchildren = defaultdict(set)
    vchildren['/'] = set()
    for m in recursive_media_search(rootdir):
        vchildren['/'].add(m.type)
        vchildren['/'+m.type].add('byTitle')
        vchildren['/'+m.type+'/byTitle'].add(m.title)
        vpaths[allpath.format(mediatype=m.type, title=m.title)] = m.base
        for tname, tvals in m.tags.items():
            for tval in tvals:
                vchildren['/'+m.type].add('by'+tname)
                vchildren['/'+m.type+'/by'+tname].add(tval)
                vchildren['/'+m.type+'/by'+tname+'/'+tval].add(m.title)
                vpaths[path.format(mediatype=m.type, tagname=tname, tagvalue=tval, title=m.title)] = m.base
    return vpaths, vchildren



if __name__ == '__main__':
    vpaths, vchildren = build_virtual_paths('/mnt/deadpool')
    print(vchildren)
    # for vpath, path in vpaths.items():
    #     print(vpath, '->', path)