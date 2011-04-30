displays
========

displays is a simple commandline tool to configure displaymodes in Mac OS X.

It is easily installed via Python's setuptools.

    $ sudo easy_install displays
       [...]

Or run `sudo python setup.py install` in the source code folder.

To list the online displays and its displaymodes, run `displays list`.

    $ displays list
    Loading CoreGraphics bindings...  done
    #0 Display 69676864 main online active builtin
      1280 x 800 @ 0.0 8 bits
      1280 x 800 @ 0.0 16 bits
      1280 x 800 @ 0.0 32 bits
       [...]
    #1 Display 1535231425 online active
      640 x 480 @ 90.0 8 bits
      640 x 480 @ 90.0 16 bits
      640 x 480 @ 90.0 32 bits
       [...]

To set the mode of a display, run `display set`.  You don't need
to specify all parameters as long as there is only one mode matching
the provided parameters.

    $ displays set -D 1 -W 1024 -H 768 -B 32
    Loading CoreGraphics bindings...  done
    More than one mode matches:
    1024 x 768 @ 90.0 32 bits
    1024 x 768 @ 96.0 32 bits
    1024 x 768 @ 60.0 32 bits
    1024 x 768 @ 70.0 32 bits
    1024 x 768 @ 75.0 32 bits
    1024 x 768 @ 85.0 32 bits
    1024 x 768 @ 100.0 32 bits
    1024 x 768 @ 120.0 32 bits

    $ display set -D 1 -W 1024 -H 1024 -N 32 -R 60
