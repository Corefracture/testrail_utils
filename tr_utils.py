import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-e", help="echo the string you use here", required=False)
args = parser.parse_args()

#print(args.echo)

