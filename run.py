"""
from pprint import pp

from src.main import Main
from src.io import FirebaseClient

Pipeline = Main(log_mode=True)

db: FirebaseClient = FirebaseClient.get_instance()
"""
"""
links = db.get_all_data("scrape-queue")
for _id in links:
    try:
        Pipeline.run(links[_id]["url"])
    except Exception as e:
        Pipeline.log.update(e, level=Pipeline.log.CRITICAL)
        db.save("scrape-failures", {_id: links[_id]})
        continue
    schema = Pipeline.schema.model_dump()
    db.save("programs-display", schema, set_index=True)
    db.delete_by_id("scrape-queue", _id)
    Pipeline.clear()
"""
"""
Pipeline.run("https://aimi.stanford.edu/education/summer-research-internship")
schema = Pipeline.schema
db.save("demo-display", schema, set_index=True)
"""