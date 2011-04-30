displays
========

displays is a simple commandline tool to configure displaymodes in Mac OS X.

It is easily installed via Python's setuptools.

    $ sudo easy_install displays
       [...]

Or run `sudo python setup.py install` in the source code folder.

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
