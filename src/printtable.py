""" A simple module to layout and print tables for console applications """

def layout_table(table):
        """ Calculate the widths of the columns to set the table t """
        ret = []
        for row in table:
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

def print_table(table, layout=None, alignment=None):
        """ Print the table

        If layout is not specified it is computed with layout_table.

        alignment is a iterable of characters to specify how columns should
        be aligned. For instance, "lrc" will align the first column to the
        left, the second to the right and the last column will be centered.
        
        If no alignment is specified, right alignment is assumed. """
        if layout is None:
                layout = layout_table(table)
        alignment = tuple() if alignment is None else tuple(alignment) 
        if len(alignment) < len(layout):
                alignment += ('r',) * (len(layout) - len(alignment))
        for row in table:
                tmp = ''
                for n, field in enumerate(row):
                        if n != 0:
                                tmp += ' '
                        if alignment[n] == 'r':
                                tmp += " "*(layout[n] - len(field)) + field
                        elif alignment[n] == 'l':
                                tmp += field + " "*(layout[n] - len(field))
                        elif alignment[n] == 'c':
                                lspace = (layout[n] - len(field)) / 2
                                rspace = layout[n] - len(field) - lspace
                                tmp += " "*lspace + field + " "*rspace
                        else:
                                raise ValueError, \
                                        "Unknown alignment %s"%alignment[n]
                print tmp
