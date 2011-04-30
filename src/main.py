import printtable
import argparse
import sys

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

def format_mode(mode):
        return (str(Q.CGDisplayModeGetWidth(mode)),
                str(Q.CGDisplayModeGetHeight(mode)),
                str(Q.CGDisplayModeGetRefreshRate(mode)),
                format_pixelEncoding(Q.CGDisplayModeCopyPixelEncoding(mode)))

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
                        if (not args.all
                                and not Q.CGDisplayModeIsUsableForDesktopGUI(
                                        mode)):
                                continue
                        prefix = ' *' if cmode == mode else ' '
                        table.append((prefix,) + format_mode(mode))
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
        if not args.all and any([Q.CGDisplayModeIsUsableForDesktopGUI(m)
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
                                        format_mode(mode))
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

def parse_args():
        parser = argparse.ArgumentParser(prog="displays")
        subparsers = parser.add_subparsers()
        
        parser_list = subparsers.add_parser('list',
                        help='List displays and modes')
        parser_list.add_argument('-a', '--all', action="store_true",
                help="List all modes, including those unsuitable"+
                        " for desktop GUI")
        parser_list.set_defaults(func=cmd_list)

        parser_set = subparsers.add_parser('set',
                        help='Set displaymode')
        parser_set.add_argument('mode', type=str, metavar='MODE',
                        help="The desired mode. Eg 1024x768@12")
        parser_set.add_argument('-D', '--display', type=int)
        parser_set.add_argument('-p', '--permanently', action="store_true",
                help="Persist the configuration over sessions")
        parser_set.add_argument('-c', '--choose', type=int, metavar='N',
                help="Choose the Nth alternative if multiple modes match "+
                             "MODE")
        parser_set.add_argument('-a', '--all', action='store_true',
                        help="Consider modes unusable for desktop GUI even "+
                                "if there are matching modes that are usable")
        parser_set.set_defaults(func=cmd_set)

        args = parser.parse_args()
        args.func(args)

def main():
        parse_args()

if __name__ == '__main__':
        main()
