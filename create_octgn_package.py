#!/usr/bin/env python3

# TODO: add module description

import sys
from arkham_sheets import read_set
from octgn_package import create_octgn_package


def main():
    if len(sys.argv) < 2:
        print("args: url of sheet containing set data")
        return

    url = sys.argv[1]
    arkhamset = read_set(url)

    path = create_octgn_package(arkhamset)
    print("Created OCTGN package: {0}".format(path))


if __name__ == '__main__':
    main()
