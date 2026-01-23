from argparse import ArgumentParser, Namespace

def main() -> None:
  parser = ArgumentParser()
  subparsers = parser.add_subparsers(title="commands", dest="command")

  scrape_parser = subparsers.add_parser("scrape", description="Runs the main scraping module")
  refresh_parser = subparsers.add_parser("refresh", description="Refreshes the database")
  
  scrape_parser.add_argument("url", help="URL to scrape info from.", type=str)
  scrape_parser.add_argument("-v", "--verbose", help="Print all actions while scraping", action="store_true")

  refresh_parser.add_argument("-v", "--verbose", help="Print all actions while scraping", action="store_true")

  args: Namespace = parser.parse_args()

  if args.command in ["scrape", "refresh"]:
    from src import Main
    from src import FirebaseClient
    from src import Refresher

    def scrape(url: str) -> None:
        if args.verbose:
          log_mode=True
        else:
          log_mode=False
        
        pipeline = Main(log_mode=log_mode)
        db = FirebaseClient.get_instance()

        pipeline.run(url)
        schema = pipeline.schema
        db.save("programs-display", schema, set_index=True)

    def refresh() -> None:
      if args.verbose:
        log_mode=True
      else:
        log_mode=False

      refresher = Refresher(Main(log_mode=log_mode))

      links = list(refresher.get_all_latest_entries("programs-display").keys())[0:-1]
      for link in links:
          refresher.run(link)
          refresher.clear()

    match args.command:
      case "scrape":
        scrape(args.url)
        
      case "refresh":
        refresh()
      
    