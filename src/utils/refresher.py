
from typing import Optional, Self
from datetime import datetime
from pprint import pp

from src.main import Main
from src.models import RootSchema
from src.io import FirebaseClient


class Refresher:
    def __init__(self, pipeline: Optional[Main] = None) -> None:
        self.pipeline = pipeline or Main()
        self.db = FirebaseClient.get_instance()
        self._all_data = {}

    def run(self, link: str, 
            hard:bool = False, 
            collection_path: str = "programs-display", 
            max_days: int = 7, 
            ignore_condition: bool=False) -> None:
        """
        Get all links from the database
        Rerun with certain preconditions for each

        Soft run:\n
        L> Only certain sections are reset\n
            L> Overview -> Subjects & Tags\n
            L> Eligibility\n
            L> Dates\n
            L> Locations\n
            L> Costs\n
            L> Metadata\n

        Hard run:\n
        L> All sections are reset
        """
        if hard:
            self._hard_run(link, collection_path, max_days, ignore_condition)
        else:
            self._soft_run(link, collection_path, max_days, ignore_condition)
        pass

    @staticmethod
    def _refresh_condition(schema: RootSchema, max_days: int) -> bool:
        """
        Decides whether or not to refresh a program
        Currently does it based on the date added (if date added is greater than the time specified)
        Args:
            schema (RootSchema): The schema from which the date added data is taken from
            max_days (int): The amount of days since the date added until an internship can be refreshed
        """
        try:
            date_added = datetime.strptime(schema.metadata.date_added, "%Y-%m-%d").date()
        except ValueError:
            # If date_added is "", a refresh is required anyway
            return True
        date_now = datetime.today().date()
        days_between = (date_now - date_added).days
        return days_between >= max_days

    def __get_all_data(self, collection_path: str) -> None:
        "Reads the database and gets all data from the specified collection path and sets the non-static variable"
        # If the database hasn't been read yet, do so
        if not collection_path in self._all_data:
            self._all_data[collection_path] = self.db.get_all_data(collection_path)

    def _get_latest_entry(self, collection_path: str, link: str) -> dict[str, dict]:
        """
        Gets the latest data entry of the specified link
        Returns:
            {id (str): data (dict)}
        """
        self.__get_all_data(collection_path)

        # Documents end with a "-" followed by a number representing the version of the doc
        # Find all data with the same link as the link provided
        docs_with_link: dict[int, dict] = {}
        for doc in self._all_data[collection_path]:
            id = "-".join(doc.split("-")[:-1])
            ver = doc.split("-")[-1]
            if link == id:
                # {version: {id: data}}
                docs_with_link[ver] = {id: self._all_data[collection_path][doc]}

        if len(docs_with_link) == 0:
            raise LookupError(f"No documents with link '{link}' found")

        max_ver: int = max(docs_with_link.keys())
        return docs_with_link[max_ver]

        """
        
        MOVE ALL DATABASE LOGIC TO HERE
        
        """


    def get_all_latest_entries(self, collection_path: str) -> dict[str, dict]:
        self.__get_all_data(collection_path)

        all_latest_entries: dict[str, dict] = {}
        for data in self._all_data[collection_path]:
            id = "-".join(data.split("-")[:-1])
            if not id in all_latest_entries:
                all_latest_entries[id] = self._get_latest_entry(collection_path, id)
        
        return all_latest_entries

    def _soft_run(self, link: str, collection_path: str, max_days: int, ignore_condition: bool) -> None:
        doc: RootSchema = RootSchema.model_validate(self._get_latest_entry(collection_path, link)[link])
        cleared_schema = RootSchema()

        # Keep some sections
        doc.overview.subject = []
        doc.overview.tags = []
        cleared_schema.overview = doc.overview
        cleared_schema.contact = doc.contact

        self.pipeline.schema = cleared_schema
        pp(self.pipeline.schema)

        if self._refresh_condition(doc, max_days) or ignore_condition:
            self.pipeline.run(link)

            schema = self.pipeline.schema.model_dump()
            self.db.save(collection_path, schema, set_index=True)
            print(f"{link} refreshed!")

    def _hard_run(self, link: str, collection_path: str, max_days: int, ignore_condition: bool) -> None:
        doc: RootSchema = RootSchema.model_validate(self._get_latest_entry(collection_path, link)[link])
        cleared_schema = RootSchema()
        self.pipeline.schema = cleared_schema
        pp(self.pipeline.schema)

        if self._refresh_condition(doc, max_days) or ignore_condition:
            self.pipeline.run(link)

            schema = self.pipeline.schema.model_dump()
            self.db.save(collection_path, schema, set_index=True)

    def clear(self) -> Self:
        pipeline = self.pipeline.clear()
        self._all_data = {}
        return type(self)(pipeline=pipeline)

if __name__ == "__main__":
    r = Refresher()
    links = list(r.get_all_latest_entries("programs-display").keys())[0:-1]
    for link in links:
        r.run(link)
        r.clear()