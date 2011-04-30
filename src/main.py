import argparse
import sys

def parse_modeString(s):
        """ Parses a modeString like '1024 x 768 @ 60' """
        refresh, width, height = None, None, None
        if '@' in s:
                s, refresh = s.split('@', 1)
                refresh = int(refresh)
        if 'x' in s:
                width, height = [int(x) for x in s.split('x', 1)]
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

def format_mode(mode):
        return  '%s x %s @ %s %s bits' % (
                Q.CGDisplayModeGetWidth(mode),
                Q.CGDisplayModeGetHeight(mode),
                Q.CGDisplayModeGetRefreshRate(mode),
                Q.CGDisplayModeCopyPixelEncoding(mode))

def load_quartz():
        # TODO why is this so slow?
        global Q
        import Quartz as Q

def cmd_list(args):
        load_quartz()
        ids = get_online_display_ids()
        for n, _id in enumerate(ids):
                Q.CGDisplayIsMain(_id)
                print '#%s Display %s %s' % (n, _id,
                                ' '.join(get_flags_of_display(_id)))
                cmode = Q.CGDisplayCopyDisplayMode(_id)
                for mode in Q.CGDisplayCopyAllDisplayModes(_id, None):
                        print ' (*)' if cmode == mode else '    ', \
                                format_mode(mode)

def cmd_set(args):
        load_quartz()
        if args.display is None:
                _id = Q.CGMainDisplayID()
        else:
                _id = get_online_display_ids()[args.display]
        width, height, refresh = parse_modeString(args.mode)
        candidates = [mode for mode
                        in Q.CGDisplayCopyAllDisplayModes(_id, None) if (
                (width is None or
                        width == Q.CGDisplayModeGetWidth(mode)) and
                (height is None or
                        height == Q.CGDisplayModeGetHeight(mode)) and
                (refresh is None or
                        refresh == Q.CGDisplayModeGetRefreshRate(mode)))]
        if len(candidates) == 0:
                print 'No supported displaymode matches'
                return
        if len(candidates) > 1 and args.choose is None:
                print 'More than one mode matches:'
                cmode = Q.CGDisplayCopyDisplayMode(_id)
                for n, mode in enumerate(candidates):
                        print n, ' (*)' if cmode == mode else '    ', \
                                format_mode(mode)
                print 'Refine the request or use --choose to choose'
                return
        r, config = Q.CGBeginDisplayConfiguration(None) 
        if(r != 0):
                print 'CGBeginDisplayConfiguration failed'
                return
        if(Q.CGConfigureDisplayWithDisplayMode(
                        config,
                        _id,
                        candidates[0 if args.choose is None else args.choose],
                        None) != 0):
                print 'CGConfigureDisplayWithDisplayMode failed'
                return
        if(Q.CGCompleteDisplayConfiguration(
                        config,
                        Q.kCGConfigurePermanently if args.permanently
                                else Q.kCGConfigureForSession)):
                print 'CGCompleteDisplayConfiguration failed'
                return
        else:
                print 'success'

def parse_args():
        parser = argparse.ArgumentParser(prog="displays")
        subparsers = parser.add_subparsers()
        
        parser_list = subparsers.add_parser('list',
                        help='List displays and modes')
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
        parser_set.set_defaults(func=cmd_set)

        args = parser.parse_args()
        args.func(args)

def main():
        parse_args()

if __name__ == '__main__':
        main()
