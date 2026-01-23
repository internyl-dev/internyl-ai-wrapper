
from src.io.databases import FirebaseClient
from src.utils.refresher import Refresher
db = FirebaseClient.get_instance()

def remove_already_scraped_links() -> None:
    all_data = db.get_all_data("scrape-queue")
    scraped = db.get_all_data("programs-display")
    scraped_urls = [db.get_link_from_id(doc_id) for doc_id in scraped]
    for data in all_data:
        if all_data[data]["url"] in scraped_urls:
            db.delete_by_id("scrape-queue", data)

def get_collection_length(collection_path: str) -> int:
    return len(db.get_all_data(collection_path))

def migrate_old_entries() -> None:
    keys = db.get_all_old_entries("programs-display").keys()
    for key in keys:
        print(f"Moved {key}")
        db.migrate("programs-display", "programs-history", key)

def refresh() -> None:
    r = Refresher()
    links = list(r.get_all_latest_entries("programs-display").keys())[0:-1]
    for link in links:
        r.run(link)
        r.clear()

migrate_old_entries()
refresh()