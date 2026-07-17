
import os
import dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from typing import Self, Optional

from src.models import RootSchema

dotenv.load_dotenv()

class FirebaseClient:
    __shared_instance:Optional[Self] = None

    def __init__(self) -> None:

        if FirebaseClient.__shared_instance:
            raise Exception("Shared instance already exists")

        # Replace with the actual path
        cred = credentials.Certificate(os.environ.get("FIREBASE_SDK_PATH"))
        firebase_admin.initialize_app(cred)

        # Get a Firestore client
        self.database = firestore.client()

        FirebaseClient.__shared_instance = self

        #self.logger.debug("Firebase Admin SDK initialized and Firestore client ready!")

    @classmethod
    def get_instance(cls) -> Self:
        if not cls.__shared_instance:
            cls()
        assert cls.__shared_instance
        return cls.__shared_instance

    @staticmethod
    def _all_data_guard(collection_path: str, all_data: Optional[dict[str, dict]] = None) -> None:
        if (collection_path=="") and (all_data is None):
            raise ValueError("Either `collection_path` or `all_data` must be given, both empty")
        
    def _get_name_index(self, 
                        collection_path: str, 
                        document: Optional[dict | RootSchema] = None,
                        link: Optional[str] = None,
                        all_data: Optional[dict[str, dict]] = None) -> str:
        """
        
        """
        if not link:
            if isinstance(document, dict):
                link = document["overview"]["link"].replace("/", "\\")
            elif isinstance(document, RootSchema):
                link = document.overview.link.replace("/", "\\")

        # Insure an id was given by at least the document or as an argument
        if link is None:
            raise ValueError("Either `document` or `link` must be given, both empty")

        self._all_data_guard(collection_path, all_data)

        documents = all_data or self.get_all_data(collection_path)
        documents_with_link = [doc_id for doc_id in documents if self.link_in_id(doc_id, link)]
        
        if not documents_with_link:
            next_index = 0
        else:
            indeces = [self.get_version_from_id(doc_id) for doc_id in documents_with_link]
            next_index = max(indeces) + 1
        
        return f"{link}-{next_index}"

    def save(self, 
             collection_path:str, 
             document:dict|RootSchema, 
             doc_id: Optional[str] = None, 
             set_index:bool=False,
             all_data: Optional[dict[str, dict]] = None) -> None:
        """
        
        """
        collection_ref = self.database.collection(collection_path)

        # Normalize
        if isinstance(document, RootSchema):
            document = document.model_dump()

        if set_index:
            document_name = self._get_name_index(collection_path, document, doc_id, all_data)
            collection_ref.document(document_name).set(document)
        elif doc_id:
            collection_ref.document(doc_id).set(document)
        else:
            update_item, doc_ref = collection_ref.add(document)

    def set(self, id:str, document:dict|RootSchema):
        pass

    def get_by_id(self, collection_path: str, doc_id:str) -> dict:
        "Returns just the data of the given ID"
        collection_ref = self.database.collection(collection_path)
        doc = collection_ref.document(doc_id).get()
        data = doc.to_dict()
        if data is not None:
            return data
        else:
            raise ValueError(f"Data of id '{doc_id}' not found")

    def get_all_data(self, collection_path:str)-> dict:
        ""
        collection_ref = self.database.collection(collection_path)
        documents = collection_ref.stream()

        return {document.id: document.to_dict() for document in documents}

    def delete_by_id(self, collection_path:str, doc_id:str) -> None:
        ""
        collection_ref = self.database.collection(collection_path)
        collection_ref.document(doc_id).delete()

    def reindex(self, collection_path: str, old_id: str) -> None:
        ""
        data = self.get_by_id(collection_path, old_id)
        self.delete_by_id(collection_path, old_id)
        self.save(collection_path, data, set_index=True)

    @staticmethod
    def get_link_from_id(doc_id: str) -> str:
        ""
        return "-".join(doc_id.split("-")[:-1])
    
    @staticmethod
    def get_version_from_id(doc_id: str) -> int:
        ""
        return int(doc_id.split("-")[-1])

    def link_in_id(self, doc_id: str, link: str) -> bool:
        ""
        return self.get_link_rom_id(doc_id) == link

    def get_latest_entry(self,  
                         link: str, 
                         collection_path: str = "",
                         all_data: Optional[dict[str, dict]] = None) -> dict[str, dict]:
        """
        Gets the latest data entry of the specified link
        Returns:
            {id (str): data (dict)}
        """
        self._all_data_guard(collection_path, all_data)

        all_data = all_data or self.get_all_data(collection_path)

        # Documents end with a "-" followed by a number representing the version of the doc
        # Find all data with the same link as the link provided
        docs_with_link: dict[int, dict] = {}
        for doc_id in all_data:
            if self.link_in_id(doc_id, link):
                # {version: {id: data}}
                ver = self.get_version_from_id(doc_id)
                docs_with_link[ver] = {doc_id: all_data[doc_id]}

        if not docs_with_link:
            raise LookupError(f"No documents with link '{link}' found")

        max_ver: int = max(docs_with_link.keys())
        return docs_with_link[max_ver]

    def get_all_latest_entries(self, 
                               collection_path: str = "", 
                               all_data: Optional[dict[str, dict]] = None) -> dict[str, dict]:
        """
        Returns all latest data entries
        Returns:
            {id (str): data (dict)}
        """
        self._all_data_guard(collection_path, all_data)

        all_data = all_data or self.get_all_data(collection_path)

        all_latest_entries: dict[str, dict] = {}
        for doc_id in all_data:
            if doc_id not in all_latest_entries:
                all_latest_entries.update(self.get_latest_entry(self.get_link_from_id(doc_id), 
                                          collection_path, 
                                          all_data))
        
        return all_latest_entries

    def get_all_old_entries(self, 
                            collection_path: str = "", 
                            all_data: Optional[dict[str, dict]] = None) -> dict[str, dict]:
        """
        
        """
        self._all_data_guard(collection_path, all_data)
        
        all_data = all_data or self.get_all_data(collection_path)
        all_latest_entries = self.get_all_latest_entries(all_data=all_data)

        return {doc_id: all_data[doc_id] for doc_id in all_data if doc_id not in all_latest_entries}

    def migrate(self, old_path, new_path, doc_id):
        old_collection_ref = self.database.collection(old_path)
        new_collection_ref = self.database.collection(new_path)

        data = self.get_by_id(old_path, doc_id)
        new_collection_ref.document(doc_id).set(data)
        old_collection_ref.document(doc_id).delete()


if __name__ == "__main__":
    #print(FirebaseClient.get_instance().get_by_id("programs-display", "0e9rDP8y6T5xNM3O2Xoj"))
    #FirebaseClient.get_instance().reindex("programs-display", "0e9rDP8y6T5xNM3O2Xoj")
    db = FirebaseClient.get_instance()
    db.save("demo", {"overview": {"link": "example.com"}}, "custom_id")
