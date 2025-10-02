import argparse
from script.core.Elves import Elves

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, default='dist/index.html')
    parser.add_argument('--debug', type=bool, default=False)

    Elves = Elves(url=parser.parse_args().url)
    Elves.run(debug=parser.parse_args().debug)
