""" Table datatype """

from collections import namedtuple

class Table(object):
        class Empty(object):
                def __str__(self):
                        return ''
        def __init__(self, data=None):
                self.rows = [] if data is None \
                        else [[field for field in row] for row in data] 
                self.empty_value = Table.Empty()
                self.metarow_field = namedtuple('meta_row_field',
                                        ['alignment', 'separator', 'key'])
                self.default_metarow_field = self.metarow_field(
                                alignment='r', separator=' ', key=None)
                self.metarow = [self.default_metarow_field]*self.width
        def __getitem__(self, key):
                assert isinstance(key, tuple) and len(key) == 2
                if isinstance(key[1], str):
                        key = (key[0], self.col_by_key(key[1]))
                return self.rows[key[0]][key[1]]
        def __setitem__(self, key, value):
                assert isinstance(key, tuple) and len(key) == 2
                if isinstance(key[1], str):
                        key = (key[0], self.col_by_key(key[1]))
                try:
                        row = self.rows[key[0]]
                except IndexError:
                        self.rows.extend(([],) * (len(self.rows) - key[0] + 1))
                        row = self.rows[-1]
                try:
                        row[key[1]] = value
                except IndexError:
                        row.extend((self.empty_value,) * (
                                len(row) - key[1] + 1))
                        row[-1] = value
        def __delitem__(self, key):
                assert isinstance(key, tuple) and len(key) == 2
                if isinstance(key[1], str):
                        key = (key[0], self.col_by_key(key[1]))
                try:
                        self.rows[key[0]][key[1]] = self.empty_value
                except IndexError:
                        pass
        def get_row(self, i):
                try:
                        return self.rows[i]
                except IndexError:
                        return []
        def set_row(self, i, row):
                try:
                        self.rows[i] = list(row)
                except IndexError:
                        self.rows.extend(([],) * (len(self.rows) - key[0]))
                        self.rows.append(list(row))
        def del_row(self, i):
                try:
                        del self.rows[i]
                except IndexError:
                        pass
        def get_col(self, i):
                if isinstance(i, str):
                        i = self.col_by_key(i)
                ret = []
                for row in self.rows:
                        try:
                                ret.append(row[i])
                        except IndexError:
                                row.append(self.empty_value)
                return ret
        def set_col(self, i, col, key=None):
                if isinstance(i, str):
                        i = self.col_by_key(i)
                for j, row in enumerate(self.rows):
                        try:
                                v = col[j]
                        except IndexError:
                                v = self.empty_value
                        try:
                                row[i] = v
                        except IndexError:
                                row.extend((self.empty_value,) * (
                                                len(row) - i))
                                row.append(col[j])
                if i >= len(self.metarow):
                        self.metarow.extend(
                                (self.default_metarow_field,) * (
                                        len(self.metarow) - i + 1))
                if key is not None:
                        self.set_key(i, key)
        def del_col(self, i):
                if isinstance(i, str):
                        i = self.col_by_key(i)
                for row in self.rows:
                        try:
                                del row[i]
                        except IndexError:
                                pass
                try:
                        del self.metarow[i]
                except IndexError:
                        pass
        def append_row(self, row):
                self.rows.append(row)
                self.metarow.append(self.default_metarow_field)
        def append_col(self, col, key=None):
                self.set_col(self.width, col, key)
        def insert_row(self, i, row):
                self.rows.insert(i, list(row))
        def insert_col(self, i, col):
                if isinstance(i, str):
                        i = self.col_by_key(i)
                for j, row in enumerate(self.rows):
                        row.insert(i, col[j])
                self.metarow.insert(i, self.default_metarow_field)
        @property
        def width(self):
                return max((len(row) for row in self.rows))
        @property
        def height(self):
                return len(self.rows)
        def __iter__(self):
                return iter(self.rows)
        def __repr__(self):
                return "Table("+repr(self.rows)+")"
        def __str__(self, layout=None, alignment=None, separators=None):
                """ Converts the table to a string

                If layout is not specified it is computed with layout_table.

		alignment is an iterable of characters to specify
		how columns should be aligned. For instance, "lrc"
		will align the first column to the left, the second
		to the right and the last column will be centered.
		If no alignment is specified, the alignment set
                with set_alignment is used.
                
		separators is an iterable of strings to separate
		the columns.  If none is specified, the separator
                set with set_separator is used.
		"""
                ret = ''
                if layout is None:
                        layout = self.layout()
                alignment = tuple() if alignment is None else tuple(alignment) 
                seps = tuple() if separators is None else tuple(separators) 
                if len(alignment) < len(layout):
                        alignment += (None,) * (len(layout) - len(alignment))
                if len(seps) < len(layout):
                        seps += (None,) * (len(layout) - len(seps))
                first = True
                for row in self.rows:
                        if first:
                                first = False
                        else:
                                ret += '\n'
                        for n, field in enumerate(row):
                                sep = self.get_separator(n) \
                                        if seps[n] is None \
                                        else seps[n]
                                if n != 0:
                                        ret += sep
                                if field is self.empty_value:
                                        field = ''
                                al = self.get_alignment(n) \
                                        if alignment[n] is None \
                                        else alignment[n]
                                if al == 'r':
                                        ret += " "*(layout[n] - len(field)
                                                        ) + field
                                elif al == 'l':
                                        ret += field + " "*(layout[n]
                                                                - len(field))
                                elif al == 'c':
                                        lspace = (layout[n] - len(field)) / 2
                                        rspace = layout[n] - len(field) - lspace
                                        ret += " "*lspace + field + " "*rspace
                                else:
                                        raise ValueError, \
                                                "Unknown alignment %s" % al
                return ret

        def layout(self):
                """ Calculate the widths of the columns to set the table """
                ret = []
                for row in self.rows:
                        if len(row) > len(ret):
                                ret += [0] * (len(row) - len(ret))
                        for n, field in enumerate(row):
                                if field is self.empty_value:
                                        field = ''
                                ret[n] = max(ret[n], len(field))
                return ret
        def set_key(self, column, key):
                self.metarow[column] = self.metarow[column]._replace(
                                        key = key)
        def get_key(self, column):
                return self.metarow[column].key
        def set_alignment(self, column, alignment):
                if isinstance(column, str):
                        column = self.col_by_key(column)
                self.metarow[column] = self.metarow[column]._replace(
                                        alignment = alignment)
        def get_alignment(self, column):
                if isinstance(column, str):
                        column = self.col_by_key(column)
                return self.metarow[column].alignment
        def set_separator(self, column, separator):
                if isinstance(column, str):
                        column = self.col_by_key(column)
                self.metarow[column] = self.metarow[column]._replace(
                                        separator = separator)
        def get_separator(self, column):
                if isinstance(column, str):
                        column = self.col_by_key(column)
                return self.metarow[column].separator
        def col_by_key(self, key):
                for i, meta in enumerate(self.metarow):
                        if key == meta.key:
                                return i
                raise IndexError, "Key not found"

def sup_of_layouts(layout1, layout2):
        """ Return the least layout compatible with layout1 and layout2 """
        if len(layout1) > len(layout2):
                layout1, layout2 = layout2, layout1
        if len(layout1) < len(layout2):
                layout1 += [0] * (len(layout2) - len(layout1))
        return [max(layout1[i], layout2[i]) for i in xrange(len(layout1))]
