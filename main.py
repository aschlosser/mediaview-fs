#!/usr/bin/env python3
import logging
import os
import os.path
import sys
import errno
import mediastore
from stat import S_IFDIR, S_IWUSR, S_IWGRP, S_IWOTH
from fuse import FUSE, FuseOSError, LoggingMixIn, Operations
from time import time

NOT_WRITE = ~ (S_IWUSR | S_IWGRP | S_IWOTH)

class Mediaview(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = root
        self.vpaths, self.vchildren = mediastore.build_virtual_paths(root)
        now = time()
        st = os.lstat(root)
        self.root_stat = dict((key, getattr(st, key)) for key in ('st_gid', 'st_nlink', 'st_size', 'st_uid'))
        self.root_stat['st_mode'] = (S_IFDIR | 0o555)
        self.root_stat['st_ctime'] = now
        self.root_stat['st_mtime'] = now
        self.root_stat['st_atime'] = now

    # Helpers
    # =======

    def is_virtual(self, path):
        return path in self.vchildren

    def convert_path(self, path):
        head = path
        tail = ''
        while not head in self.vpaths:
            if head == '/':
                raise FuseOSError(errno.ENOENT)
            head, tt = os.path.split(head)
            tail = os.path.join(tt, tail)
        if tail.endswith('/'):
            tail = tail[:-1]
        return os.path.join(self.vpaths[head], tail)

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        # we don't allow write access
        if mode & S_IWUSR > 0 or mode & S_IWGRP > 0 or mode & S_IWOTH > 0:
            raise FuseOSError(errno.EACCES)
        return 0

    def getattr(self, path, fh=None):
        if self.is_virtual(path):
            return self.root_stat
        else:
            try:
                real_path = self.convert_path(path)
                st = os.lstat(real_path)
                fstat = dict((key, getattr(st, key)) for key in
                            ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
                fstat['st_mode'] = fstat['st_mode'] & NOT_WRITE
                return fstat
            except KeyError:
                return {}

    def readdir(self, path, fh):
        if self.is_virtual(path):
            return {'.', '..'}.union(self.vchildren[path])
        else:
            real_path = self.convert_path(path)
            children = ['.', '..']
            if os.path.isdir(real_path):
                children.extend(os.listdir(real_path))
            return children

    def readlink(self, path):
        pathname = os.readlink(self.convert_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def statfs(self, path):
        st = os.statvfs(self.root)
        fstat = dict((key, getattr(st, key)) for key in
                            ('f_bsize', 'f_frsize', 'f_blocks', 'f_bfree', 'f_bavail', 'f_files', 'f_ffree', 'f_favail', 'f_namemax'))
        fstat['f_flags'] = (os.ST_RDONLY | os.ST_NODIRATIME | os.ST_NOATIME)
        return fstat


    # File methods
    # ============

    def open(self, path, flags):
        # TODO adapt and allow only read access
        real_path = self.convert_path(path)
        return os.open(real_path, flags)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    # def flush(self, path, fh):
    #     return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    # def fsync(self, path, fdatasync, fh):
    #     return self.flush(path, fh)


def main(root, mountpoint):
    logging.basicConfig(level=logging.DEBUG)
    FUSE(Mediaview(root), mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
