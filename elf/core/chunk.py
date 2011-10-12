"""
  Copyright (C) 2008-2011  Tomasz Bursztyka

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

""" ChunkCounter and Chunk classes """

class ChunkCounter( object ):
    """ Basic Singleton counter class for chunks """

    _instance = None
    count = 0

    def __new__(cls):
        """ Singleton instanciation """

        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance.count = -1

        cls._instance.count += 1

        return cls._instance


class Chunk( object ):
    """ Basic Chunk class: all parts of ELF format are assumed as chunks """

    def __init__(self, prop=None, load=False, offset=None, size=0):
        """ Constructor """

        self.prop = prop
        self.offset_start = offset
        self.offset_end = offset + size
        self.size = size
        self.data = None
        self.modified = False
        # unique reference
        self.inside = None
        # Mutltiple includes, see accessors below
        self.includes = []

        self.counter = ChunkCounter()

        if load:
            self.load()

    def __del__(self):
        """ Finalize before deletion """

        self.finalize()

    def __setattr__(self, name, value):
        """ Attribute setter rewrite """

        self.__dict__[name] = value

        if name == 'data' and value is not None:
            self.modified = True
            # Redefine the size 
            self.size = len(value)
            self.offset_end = self.offset_start + self.size

        elif name.find('offset') > -1 and value is not None:
            self.modified = True

    def load(self, offset=None, filemap=None):
        """ Loads chunk content into data attribute from filemap """

        if offset == None:
            if self.offset_start == None:
                return
            else:
                offset = self.offset_start

        if self.size <= 0:
            return

        f_m = None
        if filemap != None:
            f_m = filemap
        elif self.prop.map_src != None:
            f_m = self.prop.map_src
        else:
            return

        f_m.seek(self.offset_start)
        self.data = f_m.read(self.size)

    def remove(self, impact = False):
        """ Remove the chunk """

        pass

    def add_include(self, include):
        """ add an include to the chunk, this chunk becomes the parent """

        if include not in self.includes:
            self.includes.append(include)
            include.inside = self

    def chunks(self):
        """ Returns the chunks it possesses """

        return [self]

    def finalize(self):
        """ Decreasing the ChunkCounter """

        self.counter.count -= 1

    def write(self, filemap):
        """ Write the chunk and its includes """

        filemap.seek(self.offset_start)

        if len(self.includes) == 0:
            filemap.write(self.data)

            return self.size

        cur_data = 0
        cur_offset = self.offset_start

        for inc in self.includes:
            if cur_offset < inc.offset_start:
                filemap.write(self.data[cur_data:inc.offset_start - cur_offset])

                cur_data += inc.offset_start - cur_offset
                cur_offset = inc.offset_start

            w_size = inc._write(filemap)

            cur_data += w_size
            cur_offset += w_size

        return cur_data

#######
# EOF #
#######

