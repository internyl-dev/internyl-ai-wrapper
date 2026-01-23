from argparse import ArgumentParser, Namespace

from main import Main
from io.databases import FirebaseClient
from utils.refresher import Refresher

def main() -> None:
  parser = ArgumentParser()
  subparsers = parser.add_subparsers(title="commands", dest="command")

  scrape_parser = subparsers.add_parser("scrape", description="Runs the main scraping module")
  refresh_parser = subparsers.add_parser("refresh", description="Refreshes the database")
  
  scrape_parser.add_argument("url", help="URL to scrape info from.", type=str)
  scrape_parser.add_argument("-v", "--verbose", help="Print all actions while scraping", action="store_true")

  args: Namespace = parser.parse_args()

  if args.command == "scrape":
    if args.verbose:
      log_mode=True
    else:
      log_mode=False
    
    pipeline = Main(log_mode=log_mode)
    db = FirebaseClient.get_instance()

    pipeline.run(args.url)
    schema = pipeline.schema
    db.save("programs-display", schema, set_index=True)

    