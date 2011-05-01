displays
========

displays is a simple commandline tool to configure displaymodes and
mirroring in Mac OS X.

It is easily installed via Python's setuptools.

    $ sudo easy_install displays
       [...]

Or run `sudo python setup.py install` in the source code folder.

Configuring display modes
-------------------------

To list the online displays and its displaymodes, run `displays list`.

        $ displays list
        #0 display 69676864 main online active builtin
         * 1280  800   0.0 24b
           1152  720   0.0 24b
           1024  768   0.0 24b
           1024  768   0.0 24b
           1024  640   0.0 24b
            800  600   0.0 24b
            800  600   0.0 24b

To set the mode of a display, run `display set`.

        $ displays set 1280x800

If several modes match the same modeline, you can pick one
using the `--choose` option.

        $ displays set 1024x
        More than one mode matches:

          0 1024 768 0.0 24b
          1 1024 768 0.0 24b
          2 1024 640 0.0 24b

        Refine the request or use `--choose n' to pick canididate n
        $ displays set 1024x --choose 2

Displaymodes that Mac OS X thinks are not suitable for the desktop GUI
are hidden.  Use `-all` (`-a`) to involve them.

To change the mode of another display, use the option `--display`.  Example:

        $ displays set 1280x1024@75 --display 1

Changes persist for the duration of the loginsession.  To apply the
changes for every session, use the `--permanently` flag.

Configuring mirroring
---------------------
A bunch of displays that show the same image are called a mirroring set.
If you want display #0 to be in the same mirroring set as display #1, run:

        $ displays mirror --display 0 --master 1

If you do not specify `--display` or `--master`, the master display
and the first other display will be mirrored.

To remove display #1 from a mirroring set, run:

        $ displays unmirror --display 1

If you do not specify `--display` then the main display will be unmirrored if
it is in a display set. Otherwise another display in a mirroring set will
be unmirrored.
