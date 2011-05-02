import printtable
import argparse
import sys

# From IOKit/IOGraphicsTypes.h
IOFLAGS = {
        'valid':        0x000001,
        'safe':         0x000002,
        'default':      0x000003,
        'always_show':  0x000008,
        'never_show':   0x000010,
        'not_resize':   0x000020,
        'interlaced':   0x000040,
        'simulscan':    0x000100,
        'not_preset':   0x000200,
        'builtin':      0x000400,
        'stretched':    0x000800,
        'not_gfx_qual': 0x001000,
        'val_ag_dply':  0x002000,
        'tv':           0x100000,
        'mirroring_ok': 0x200000 }

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

def format_mode(mode, show_flags=False):
        ret = (str(Q.CGDisplayModeGetWidth(mode)),
               str(Q.CGDisplayModeGetHeight(mode)),
               str(Q.CGDisplayModeGetRefreshRate(mode)),
               format_pixelEncoding(Q.CGDisplayModeCopyPixelEncoding(mode)))
        if show_flags:
                flags = Q.CGDisplayModeGetIOFlags(mode)
                flagbit = ''
                first = True
                for name, flag in IOFLAGS.iteritems():
                        if flags & flag == 0:
                                continue
                        if first:
                                first = False
                        else:
                                flagbit += ' '
                        flagbit += name
                ret += (flagbit,)
        return ret

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
                Q.CGDisplayIsMain(_id)
                headlines.append('#%s display %s %s' % (n, _id,
                                ' '.join(get_flags_of_display(_id))))
                cmode = Q.CGDisplayCopyDisplayMode(_id)
                table = []
                for mode in sorted(Q.CGDisplayCopyAllDisplayModes(_id, None),
                                        cmp=cmp_mode):
                        if (not args.all_modes
                                and not Q.CGDisplayModeIsUsableForDesktopGUI(
                                        mode)):
                                continue
                        prefix = ' *' if cmode == mode else ' '
                        table.append((prefix,) + format_mode(mode, args.flags))
                tables.append(table)
        layout = reduce(printtable.sup_of_layouts,
                        map(printtable.layout_table, tables), [])
        for i, table in enumerate(tables):
                print
                print headlines[i]
                printtable.print_table(table, layout=layout)

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
                table = []
                for n, mode in enumerate(candidates):
                        table.append((' *' if cmode == mode else ' ', str(n)) +
                                        format_mode(mode, args.flags))
                printtable.print_table(table)
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
        parser_list.add_argument('-f', '--flags', action="store_true",
                help="Show IO flags")
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
        parser_set.add_argument('-f', '--flags', action="store_true",
                help="Show IO flags, when displaying modes")
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
