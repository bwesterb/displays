import argparse
import sys

# TODO why is this so slow?
#      Only importing the function I need does not speed it up
print 'Loading CoreGraphics bindings... ',
sys.stdout.flush()
from Quartz import *
print 'done'

def get_online_display_ids():
        N = 3
        while True:
                v, ids, cnt = CGGetOnlineDisplayList(N, None, None)
                if cnt < N:
                        return sorted(ids)
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
                        mode['Width'],
                        mode['Height'],
                        mode['RefreshRate'],
                        mode['BitsPerPixel'])

def cmd_list(args):
        ids = get_online_display_ids()
        for n, _id in enumerate(ids):
                CGDisplayIsMain(_id)
                print '#%s Display %s %s' % (n, _id,
                                ' '.join(get_flags_of_display(_id)))
                for mode in CGDisplayAvailableModes(_id):
                        print ' ', format_mode(mode)

def cmd_set(args):
        if args.display is None:
                _id = CGMainDisplayID()
        else:
                _id = get_online_display_ids()[args.display]

        candidates = [mode for mode in CGDisplayAvailableModes(_id)
                if ((args.width is None or
                                args.width == mode['Width']) and
                        (args.height is None or
                                args.height == mode['Height']) and
                        (args.depth is None or
                                args.depth == mode['BitsPerPixel']) and
                        (args.refresh is None or
                                args.refresh == mode['RefreshRate']))]
        if len(candidates) == 0:
                print 'No supported displaymode matches'
                return
        if len(candidates) > 1:
                print 'More than one mode matches:'
                for mode in candidates:
                        print format_mode(mode)
                return
        r, config = CGBeginDisplayConfiguration(None) 
        if(r != 0):
                print 'CGBeginDisplayConfiguration failed'
                return
        CGConfigureDisplayMode(config, _id, candidates[0])
        CGCompleteDisplayConfiguration(config, kCGConfigureForSession)

def parse_args():
        parser = argparse.ArgumentParser(prog="displays")
        subparsers = parser.add_subparsers()
        
        parser_list = subparsers.add_parser('list',
                        help='List displays and modes')
        parser_list.set_defaults(func=cmd_list)

        parser_set = subparsers.add_parser('set',
                        help='Set displaymode')
        parser_set.add_argument('-W', '--width', type=int)
        parser_set.add_argument('-H', '--height', type=int)
        parser_set.add_argument('-R', '--refresh', type=int)
        parser_set.add_argument('-B', '--depth', type=int)
        parser_set.add_argument('-D', '--display', type=int)
        parser_set.set_defaults(func=cmd_set)

        args = parser.parse_args()
        args.func(args)

def main():
        parse_args()

if __name__ == '__main__':
        main()
