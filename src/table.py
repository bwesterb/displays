""" Table datatype """

class Table(object):
        class Empty(object):
                pass
        def __init__(self, data=None):
                self.rows = [] if data is None \
                        else [[field for field in row] for row in data] 
                self.empty_value = Table.Empty()
        def __getitem__(self, key):
                assert isinstance(key, tuple) and len(key) == 2
                return self.rows[key[0]][key[1]]
        def __setitem__(self, key, value):
                assert isinstance(key, tuple) and len(key) == 2
                try:
                        row = self.rows[key[0]]
                except IndexError:
                        self.rows.extend(([],) * (len(self.rows) - key[0]))
                        row = self.rows[-1]
                try:
                        row[key[1]] = value
                except IndexError:
                        row.extend((self.empty_value,) * (len(row) - key[1]))
                        row[-1] = value
        def __delitem__(self, key):
                assert isinstance(key, tuple) and len(key) == 2
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
                        self.rows.extend(([],) * (len(self.rows) - key[0] - 1))
                        self.rows.append(list(row))
        def del_row(self, i):
                try:
                        del self.rows[i]
                except IndexError:
                        pass
        def get_col(self, i):
                ret = []
                for row in self.rows:
                        try:
                                row.append(row[i])
                        except IndexError:
                                row.append(self.empty_value)
                return ret
        def set_col(self, i, col):
                for row in self.rows:
                        try:
                                row[i] = col[i]
                        except IndexError:
                                row.extend((self.empty_value,) * (
                                                len(row) - i - 1))
                                row.append(col[i])
        def del_col(self, i):
                for row in self.rows:
                        try:
                                del row[i]
                        except IndexError:
                                pass
        def append_row(self, row):
                self.rows.append(row)
        def append_col(self, col):
                self.set_col(self.width, col)
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
		If no alignment is specified, right alignment is
		assumed.
                
		separators is an iterable of strings to separate
		the columns.  If none is specified, ' ' is assumed.
		"""
                ret = ''
                if layout is None:
                        layout = self.layout()
                alignment = tuple() if alignment is None else tuple(alignment) 
                seps = tuple() if separators is None else tuple(separators) 
                if len(alignment) < len(layout):
                        alignment += ('r',) * (len(layout) - len(alignment))
                if len(seps) < len(layout):
                        seps += (' ',) * (len(layout) - len(seps))
                first = True
                for row in self.rows:
                        if first:
                                first = False
                        else:
                                ret += '\n'
                        for n, field in enumerate(row):
                                if n != 0:
                                        ret += seps[n]
                                if alignment[n] == 'r':
                                        ret += " "*(layout[n] - len(field)
                                                        ) + field
                                elif alignment[n] == 'l':
                                        ret += field + " "*(layout[n]
                                                                - len(field))
                                elif alignment[n] == 'c':
                                        lspace = (layout[n] - len(field)) / 2
                                        rspace = layout[n] - len(field) - lspace
                                        ret += " "*lspace + field + " "*rspace
                                else:
                                        raise ValueError, \
                                                "Unknown alignment %s" % \
                                                        alignment[n]
                return ret

        def layout(self):
                """ Calculate the widths of the columns to set the table """
                ret = []
                for row in self.rows:
                        if len(row) > len(ret):
                                ret += [0] * (len(row) - len(ret))
                        for n, field in enumerate(row):
                                ret[n] = max(ret[n], len(field))
                return ret

def sup_of_layouts(layout1, layout2):
        """ Return the least layout compatible with layout1 and layout2 """
        if len(layout1) > len(layout2):
                layout1, layout2 = layout2, layout1
        if len(layout1) < len(layout2):
                layout1 += [0] * (len(layout2) - len(layout1))
        return [max(layout1[i], layout2[i]) for i in xrange(len(layout1))]
