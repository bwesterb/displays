import argparse
import table
import sys

# From IOKit/IOGraphicsTypes.h
IOFLAGS = {
        'Valid':                0x000001,
        'Safe':                 0x000002,
        'Default':              0x000003,
        'AlwaysShow':           0x000008,
        'NeverShow':            0x000010,
        'NotResize':            0x000020,
        'Interlaced':           0x000040,
        'Simulscan':            0x000100,
        'NotPreset':            0x000200,
        'Builtin':              0x000400,
        'Stretched':            0x000800,
        'NotGfxQual':           0x001000,
        'ValidAgainstDisplay':  0x002000,
        'TV':                   0x100000,
        'MirroringIsOK':        0x200000 }

def cmp_mode(b, a):
        """ A comparison function for displaymodes """
        tmp = cmp(Q.CGDisplayModeIsUsableForDesktopGUI(a),
                  Q.CGDisplayModeIsUsableForDesktopGUI(b))
        if tmp != 0: return tmp
        tmp = cmp(guess_bitDepth(Q.CGDisplayModeCopyPixelEncoding(a)),
                  guess_bitDepth(Q.CGDisplayModeCopyPixelEncoding(b)))
        if tmp != 0: return tmp
        tmp = cmp(Q.CGDisplayModeGetHeight(a) * Q.CGDisplayModeGetWidth(a),
                  Q.CGDisplayModeGetHeight(b) * Q.CGDisplayModeGetWidth(b))
        if tmp != 0: return tmp
        tmp = cmp(Q.CGDisplayModeGetHeight(a),
                  Q.CGDisplayModeGetHeight(b))
        if tmp != 0: return tmp
        tmp = cmp(Q.CGDisplayModeGetWidth(a),
                  Q.CGDisplayModeGetWidth(b))
        if tmp != 0: return tmp
        return cmp(Q.CGDisplayModeGetRefreshRate(a),
                   Q.CGDisplayModeGetRefreshRate(b))

def parse_modeString(s):
        """ Parses a modeString like '1024 x 768 @ 60' """
        refresh, width, height = None, None, None
        if '@' in s:
                s, refresh = s.split('@', 1)
                refresh = int(refresh)
        if 'x' in s:
                width, height = [int(x) if x.strip() else None
                                        for x in s.split('x', 1)]
        elif s.strip():
                width = int(s)
        else:
                width = None
        return (width, height, refresh)

def get_online_display_ids():
        N = 3
        while True:
                # NOTE
                # We assume CGGetOnlineDisplayList returns the displays
                # in the same order on a second call.
                v, ids, cnt = Q.CGGetOnlineDisplayList(N, None, None)
                if cnt < N:
                        return ids
                N *= 2

def get_flags_of_display(_id):
        ret = []
        if Q.CGDisplayIsMain(_id):
                ret.append('main')
        if Q.CGDisplayIsOnline(_id):
                ret.append('online')
        if Q.CGDisplayIsActive(_id):
                ret.append('active')
        if Q.CGDisplayIsBuiltin(_id):
                ret.append('builtin')
        if Q.CGDisplayIsCaptured(_id):
                ret.append('captured')
        if Q.CGDisplayIsInMirrorSet(_id):
                ret.append('in_mirrorset')
        if Q.CGDisplayIsStereo(_id):
                ret.append('stereo')
        return ret

def guess_bitDepth(enc):
        if enc == 'PPPPPPPP':
                return 8
        if enc == '-RRRRRGGGGGBBBBB':
                return 15
        if enc == '--------RRRRRRRRGGGGGGGGBBBBBBBB':
                return 24
        if enc == '--RRRRRRRRRRGGGGGGGGGGBBBBBBBBBB':
                return 30
        return None

def format_pixelEncoding(enc):
        depth = guess_bitDepth(enc)
        if depth is None:
                return 'unknown: %s' % enc
        return str(depth) + 'b'

def shorter_float_str(f):
        """ Converts a float to a string like str, but omits trailing .0 """
        if f.is_integer():
                return str(int(f))
        return str(f)

def get_flags_of_mode(mode):
        flags = Q.CGDisplayModeGetIOFlags(mode)
        ret = []
        for name, flag in IOFLAGS.iteritems():
                if flags & flag == 0:
                        continue
                ret.append(name)
        return ret

def format_modes(modes, full_modes=False, current_mode=None):
        """ Creates a nice readily printable Table for a list of modes.
            Used in `displays list' and the candidates list
            in `displays set'. """
        t = table.Table(((
                '*' if mode == current_mode else '',                         # 0
                str(Q.CGDisplayModeGetWidth(mode)),                          # 1
                str(Q.CGDisplayModeGetHeight(mode)),                         # 2
                '@'+shorter_float_str(Q.CGDisplayModeGetRefreshRate(mode)),  # 3
                format_pixelEncoding(
                                Q.CGDisplayModeCopyPixelEncoding(mode)))     # 4
                        for mode in modes))
        t.set_key(2, 'height')
        t.set_key(3, 'rate')
        t.set_key(4, 'depth')
        t.set_alignment('height', 'l')
        t.set_alignment('rate', 'l')
        t.set_separator('height', ' x ')
        created_flags_col = False
        if full_modes:
                t.append_col(tuple((' '.join(get_flags_of_mode(mode))
                                        for mode in modes)), key='flags')
                created_flags_col = True
        else:
                # Remove refresh rate and bit depth if they are all the same
                if len(frozenset(t.get_col('rate'))) == 1:
                        t.del_col('rate')
                if len(frozenset(t.get_col('depth'))) == 1:
                        t.del_col('depth')

                # Show distinct IO flags when several modes appear the same
                lut = {}
                for i, row in enumerate(t):
                        row = tuple(row)
                        if row not in lut:
                                lut[row] = []
                        elif not created_flags_col:
                                t.append_col(('',) * len(modes), key='flags')
                        lut[row].append(i)
                for rw, indices in lut.iteritems():
                        if len(indices) == 1:
                                continue
                        flags = {}
                        for i in indices:
                                flags[i] = get_flags_of_mode(modes[i])
                        common_flags = reduce(lambda x, y: x.intersection(y),
                                        map(frozenset, flags.itervalues()))
                        for i in indices:
                                t[i, 'flags'] = ' '.join(frozenset(flags[i])
                                                        - common_flags)
        if created_flags_col:
                t.set_alignment('flags', 'l')
        return t

def load_quartz():
        # TODO why is this so slow?
        global Q
        import Quartz as Q

def cmd_list(args):
        load_quartz()
        ids = get_online_display_ids()
        tables = []
        headlines = []
        for n, _id in enumerate(ids):
                headlines.append('#%s display %s %s' % (n, _id,
                                ' '.join(get_flags_of_display(_id))))
                cmode = Q.CGDisplayCopyDisplayMode(_id)
                modes = sorted(Q.CGDisplayCopyAllDisplayModes(
                                        _id, None), cmp=cmp_mode)
                if not args.all_modes:
                        modes = filter(Q.CGDisplayModeIsUsableForDesktopGUI,
                                                modes)
                tables.append(format_modes(modes, current_mode=cmode,
                                                full_modes=args.full_modes))
        layout = reduce(table.sup_of_layouts,
                        [t.layout() for t in tables], [])
        for i, t in enumerate(tables):
                print
                print headlines[i]
                print t.__str__(layout=layout)

def cmd_set(args):
        load_quartz()
        if args.display is None:
                _id = Q.CGMainDisplayID()
        else:
                _id = get_online_display_ids()[args.display]
        width, height, refresh = parse_modeString(args.mode)
        candidates = sorted([mode for mode
                        in Q.CGDisplayCopyAllDisplayModes(_id, None) if (
                (width is None or
                        width == Q.CGDisplayModeGetWidth(mode)) and
                (height is None or
                        height == Q.CGDisplayModeGetHeight(mode)) and
                (refresh is None or
                        refresh == Q.CGDisplayModeGetRefreshRate(mode)))],
                                        cmp_mode)
        # If there is a candidate that is usable for desktop GUI,
        # we will filter out the candidates that are not usable.
        if not args.all_modes and any([Q.CGDisplayModeIsUsableForDesktopGUI(m)
                        for m in candidates]):
                candidates = filter(Q.CGDisplayModeIsUsableForDesktopGUI,
                                        candidates)
        if len(candidates) == 0:
                print 'No supported displaymode matches'
                return -1
        if len(candidates) > 1 and args.choose is None:
                print 'More than one mode matches:'
                print
                cmode = Q.CGDisplayCopyDisplayMode(_id)
                t = format_modes(candidates, full_modes=args.full_modes,
                                        current_mode=cmode)
                t.insert_col(0, map(str, xrange(t.height)))
                print t
                print
                print 'Refine the request or use `--choose n\' to pick '+ \
                                'canididate n'
                return -2
        r, config = Q.CGBeginDisplayConfiguration(None) 
        if(r != 0):
                print 'CGBeginDisplayConfiguration failed'
                return -3
        if(Q.CGConfigureDisplayWithDisplayMode(
                        config,
                        _id,
                        candidates[0 if args.choose is None else args.choose],
                        None) != 0):
                print 'CGConfigureDisplayWithDisplayMode failed'
                return -4
        if(Q.CGCompleteDisplayConfiguration(
                        config,
                        Q.kCGConfigurePermanently if args.permanently
                                else Q.kCGConfigureForSession)):
                print 'CGCompleteDisplayConfiguration failed'
                return -5

def cmd_mirror(args):
        load_quartz()

        # Find the default values for _id and _mid
        ids = get_online_display_ids()
        main_id = Q.CGMainDisplayID()
        if len(ids) == 1:
                print 'There is only one display'
                return -6
        if args.master is None:
                _mid = main_id
        else:
                _mid = ids[args.master]
        if args.display is None:
                if _mid != main_id:
                        _id = main_id
                else:
                        _id = [i for i in ids if i != _mid][0]
        else:
                _id = ids[args.display]

        # Do the mirroring
        r, config = Q.CGBeginDisplayConfiguration(None)
        if(r != 0):
                print 'CGBeginDisplayConfiguration failed'
                return -3
        if(Q.CGConfigureDisplayMirrorOfDisplay(config, _id, _mid) != 0):
                print 'CGConfigureDisplayMirrorOfDisplay failed'
                return -7
        if(Q.CGCompleteDisplayConfiguration(
                        config,
                        Q.kCGConfigurePermanently if args.permanently
                                else Q.kCGConfigureForSession)):
                print 'CGCompleteDisplayConfiguration failed'
                return -8

def cmd_unmirror(args):
        load_quartz()
        
        # Find the display to be unmirrored
        ids = [i for i in get_online_display_ids()
                        if Q.CGDisplayIsInMirrorSet(i)]
        if len(ids) == 0:
                print 'There are no mirrored displays'
                return -9
        if args.display is None:
                main_id = Q.CGMainDisplayID()
                if main_id in ids:
                        _id = main_id
                else:
                        _id = ids[0]
        else:
                _id = get_online_display_ids()[args.display]
                if _id not in ids:
                        print 'The specified display is not in a mirroring set'
                        return -10

        # Do it
        r, config = Q.CGBeginDisplayConfiguration(None)
        if(r != 0):
                print 'CGBeginDisplayConfiguration failed'
                return -3
        if(Q.CGConfigureDisplayMirrorOfDisplay(config, _id,
                        Q.kCGNullDirectDisplay) != 0):
                print 'CGConfigureDisplayMirrorOfDisplay failed'
                return -11
        if(Q.CGCompleteDisplayConfiguration(
                        config,
                        Q.kCGConfigurePermanently if args.permanently
                                else Q.kCGConfigureForSession)):
                print 'CGCompleteDisplayConfiguration failed'
                return -12

def parse_args():
        parser = argparse.ArgumentParser(prog="displays",
                description="""
                displays allows you to list displays, set displaymodes
                and configure mirroring on Mac OS X.
                """)
        subparsers = parser.add_subparsers(title='commands')
        
        # displays list
        parser_list = subparsers.add_parser('list',
                description="""
                Lists all online displays and their display modes.
                The currently active displaymode is prefixed by a *.
                Modes that Apple thinks are unusable for a desktop GUI
                are hidden.  Use `--all-modes' to show them. """,
                        help='List displays and modes')
        parser_list.add_argument('-a', '--all-modes', action="store_true",
                help="List all modes, including those unsuitable"+
                        " for desktop GUI")
        parser_list.add_argument('-f', '--full-modes', action="store_true",
                help="Show full modes")
        parser_list.set_defaults(func=cmd_list)

        # displays set
        parser_set = subparsers.add_parser('set',
                description="""
                Sets the mode of a given display. If no display is
                specified, the main display is assumed. If multiple
                displaymodes match the modestring, you can choose one
                with `--choose'.
		Some displaymodes are deemed unusable for desktop
		GUI by Apple. They are automatically hidden from
		the list of candidates if there are usable modes
		among them. Use `--all-modes' to override. """,
                help='Set mode (resolution, refresh rate, etc.) of display')
        parser_set.add_argument('mode', type=str, metavar='MODE',
                        help="The desired mode. Eg 1024x768@12")
        parser_set.add_argument('-D', '--display', type=int)
        parser_set.add_argument('-p', '--permanently', action="store_true",
                help="Persist the configuration over sessions")
        parser_set.add_argument('-c', '--choose', type=int, metavar='N',
                help="Choose the Nth alternative if multiple modes match "+
                             "MODE")
        parser_set.add_argument('-a', '--all-modes', action='store_true',
                        help="Consider modes unusable for desktop GUI even "+
                                "if there are matching modes that are usable")
        parser_set.add_argument('-f', '--full-modes', action="store_true",
                help="Show full modes")
        parser_set.set_defaults(func=cmd_set)

        # displays mirror
        parser_mirror = subparsers.add_parser('mirror',
                description="""
                Displays that show the same image are in the same mirroring set.
                This command add the specified display to the mirroring set
                of another display.
                If no displays are specified, the main display and
                the first other display are assumed.  """,
                        help='Add a display to a mirror set')
        parser_mirror.add_argument('-d', '--display', type=int,
                        help="The DISPLAY to add to the mirroring set")
        parser_mirror.add_argument('-m', '--master', type=int,
                        metavar='DISPLAY',
                        help="A DISPLAY already in the mirroring set")
        parser_mirror.add_argument('-p', '--permanently', action="store_true",
                help="Persist the configuration over sessions")
        parser_mirror.set_defaults(func=cmd_mirror)

        # displays unmirror
        parser_unmirror = subparsers.add_parser('unmirror',
                description="""
                Displays that show the same image are in the same mirroring set.
                This command removes a specified display from its mirroring
                set.
                If no displays are specified, the main display is assumed.
                If the main display isn't mirrored, the first other display
                that *is* in a mirroring set is assumed.""",
                        help='Remove a display from its mirror set')
        parser_unmirror.add_argument('-d', '--display', type=int,
                        help="The DISPLAY to be removed from its mirrorset")
        parser_unmirror.add_argument('-p', '--permanently', action="store_true",
                help="Persist the configuration over sessions")
        parser_unmirror.set_defaults(func=cmd_unmirror)

        args = parser.parse_args()
        return args

def main():
        args = parse_args()
        return args.func(args)

if __name__ == '__main__':
        sys.exit(main())
