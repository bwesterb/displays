import argparse
import sys

# TODO why is this so slow?
#      Only importing the function I need does not speed it up
print 'Loading CoreGraphics bindings... ',
sys.stdout.flush()
from Quartz import *
print 'done'

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
                v, ids, cnt = CGGetOnlineDisplayList(N, None, None)
                if cnt < N:
                        return ids
                N *= 2

def get_flags_of_display(_id):
        ret = []
        if CGDisplayIsMain(_id):
                ret.append('main')
        if CGDisplayIsOnline(_id):
                ret.append('online')
        if CGDisplayIsActive(_id):
                ret.append('active')
        if CGDisplayIsBuiltin(_id):
                ret.append('builtin')
        if CGDisplayIsCaptured(_id):
                ret.append('captured')
        if CGDisplayIsInMirrorSet(_id):
                ret.append('in_mirrorset')
        if CGDisplayIsStereo(_id):
                ret.append('stereo')
        return ret

def format_mode(mode):
        return  '%s x %s @ %s %s bits' % (
                CGDisplayModeGetWidth(mode),
                CGDisplayModeGetHeight(mode),
                CGDisplayModeGetRefreshRate(mode),
                CGDisplayModeCopyPixelEncoding(mode))

def cmd_list(args):
        ids = get_online_display_ids()
        for n, _id in enumerate(ids):
                CGDisplayIsMain(_id)
                print '#%s Display %s %s' % (n, _id,
                                ' '.join(get_flags_of_display(_id)))
                cmode = CGDisplayCopyDisplayMode(_id)
                for mode in CGDisplayCopyAllDisplayModes(_id, None):
                        print ' (*)' if cmode == mode else '    ', \
                                format_mode(mode)

def cmd_set(args):
        if args.display is None:
                _id = CGMainDisplayID()
        else:
                _id = get_online_display_ids()[args.display]
        width, height, refresh = parse_modeString(args.mode)
        candidates = [mode for mode
                        in CGDisplayCopyAllDisplayModes(_id, None) if (
                (width is None or
                        width == CGDisplayModeGetWidth(mode)) and
                (height is None or
                        height == CGDisplayModeGetHeight(mode)) and
                (refresh is None or
                        refresh == CGDisplayModeGetRefreshRate(mode)))]
        if len(candidates) == 0:
                print 'No supported displaymode matches'
                return
        if len(candidates) > 1 and args.choose is None:
                print 'More than one mode matches:'
                cmode = CGDisplayCopyDisplayMode(_id)
                for n, mode in enumerate(candidates):
                        print n, ' (*)' if cmode == mode else '    ', \
                                format_mode(mode)
                print 'Refine the request or use --choose to choose'
                return
        r, config = CGBeginDisplayConfiguration(None) 
        if(r != 0):
                print 'CGBeginDisplayConfiguration failed'
                return
        if(CGConfigureDisplayWithDisplayMode(
                        config,
                        _id,
                        candidates[0 if args.choose is None else args.choose],
                        None) != 0):
                print 'CGConfigureDisplayWithDisplayMode failed'
                return
        if(CGCompleteDisplayConfiguration(
                        config,
                        kCGConfigureForSession)):
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
