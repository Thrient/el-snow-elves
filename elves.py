import argparse
from multiprocessing import freeze_support

from script.core.Elves import Elves

if __name__ == '__main__':
    freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, default="https://nas.elarion.cn:5277")
    parser.add_argument('--debug', type=bool, default=False)

    Elves = Elves(url=parser.parse_args().url)
    Elves.run(debug=parser.parse_args().debug)
