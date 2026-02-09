"""
Firebase service for data persistence.
Falls back to in-memory storage if Firebase is not configured.
"""
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
import json


class InMemoryStorage:
    """In-memory storage for development/testing."""

    def __init__(self):
        self.users: Dict[str, dict] = {}
        self.documents: Dict[str, dict] = {}
        self.threads: Dict[str, dict] = {}
        self.memories: Dict[str, dict] = {}  # {document_id}_{agent_id} -> memory

    def get_user(self, user_id: str) -> Optional[dict]:
        return self.users.get(user_id)

    def create_user(self, user_id: str) -> dict:
        user = {
            "userId": user_id,
            "createdAt": datetime.utcnow().isoformat(),
            "documents": []
        }
        self.users[user_id] = user
        return user

    def get_or_create_user(self, user_id: str) -> dict:
        user = self.get_user(user_id)
        if user is None:
            user = self.create_user(user_id)
        return user

    def save_document(self, document: dict) -> str:
        doc_id = document["documentId"]
        self.documents[doc_id] = document

        # Update user's document list
        user_id = document["userId"]
        if user_id in self.users:
            if doc_id not in self.users[user_id]["documents"]:
                self.users[user_id]["documents"].append(doc_id)

        return doc_id

    def get_document(self, document_id: str) -> Optional[dict]:
        return self.documents.get(document_id)

    def get_user_documents(self, user_id: str) -> List[dict]:
        user = self.get_user(user_id)
        if user is None:
            return []
        return [
            self.documents[doc_id]
            for doc_id in user.get("documents", [])
            if doc_id in self.documents
        ]

    def delete_document(self, document_id: str) -> bool:
        if document_id in self.documents:
            doc = self.documents[document_id]
            user_id = doc.get("userId")

            # Remove from user's document list
            if user_id and user_id in self.users:
                docs = self.users[user_id].get("documents", [])
                if document_id in docs:
                    docs.remove(document_id)

            # Delete associated threads
            threads_to_delete = [
                tid for tid, t in self.threads.items()
                if t.get("documentId") == document_id
            ]
            for tid in threads_to_delete:
                del self.threads[tid]

            del self.documents[document_id]
            return True
        return False

    def save_thread(self, thread: dict) -> str:
        thread_id = thread["threadId"]
        self.threads[thread_id] = thread
        return thread_id

    def get_thread(self, thread_id: str) -> Optional[dict]:
        return self.threads.get(thread_id)

    def get_document_threads(self, document_id: str) -> List[dict]:
        return [
            t for t in self.threads.values()
            if t.get("documentId") == document_id
        ]

    def add_message_to_thread(self, thread_id: str, message: dict) -> bool:
        thread = self.get_thread(thread_id)
        if thread is None:
            return False
        thread["messages"].append(message)
        thread["updatedAt"] = datetime.utcnow().isoformat()
        return True

    # Memory operations
    def get_agent_memory(self, document_id: str, agent_id: str) -> Optional[dict]:
        key = f"{document_id}_{agent_id}"
        return self.memories.get(key)

    def save_agent_memory(self, memory: dict) -> str:
        document_id = memory["documentId"]
        agent_id = memory["agentId"]
        key = f"{document_id}_{agent_id}"
        self.memories[key] = memory
        return key

    def delete_document_memories(self, document_id: str) -> int:
        """Delete all memories for a document. Returns count deleted."""
        keys_to_delete = [k for k in self.memories.keys() if k.startswith(f"{document_id}_")]
        for key in keys_to_delete:
            del self.memories[key]
        return len(keys_to_delete)

    def get_document_memories(self, document_id: str) -> List[dict]:
        """Get all agent memories for a document."""
        return [
            m for k, m in self.memories.items()
            if k.startswith(f"{document_id}_")
        ]


class FirebaseService:
    """
    Firebase service wrapper.
    Uses in-memory storage if Firebase credentials are not configured.
    """

    def __init__(self):
        self._storage: Optional[InMemoryStorage] = None
        self._db = None
        self._bucket = None
        self._initialized = False

    def _ensure_initialized(self):
        """Initialize storage on first use."""
        if self._initialized:
            return

        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if credentials_path and os.path.exists(credentials_path):
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore, storage

                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                })
                self._db = firestore.client()
                self._bucket = storage.bucket() if os.getenv('FIREBASE_STORAGE_BUCKET') else None
                print("Firebase initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Firebase: {e}")
                print("Falling back to in-memory storage")
                self._storage = InMemoryStorage()
        else:
            print("Firebase credentials not found. Using in-memory storage.")
            self._storage = InMemoryStorage()

        self._initialized = True

    @property
    def is_using_firebase(self) -> bool:
        self._ensure_initialized()
        return self._db is not None

    # User operations
    def get_user(self, user_id: str) -> Optional[dict]:
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_user(user_id)
        doc = self._db.collection('users').document(user_id).get()
        return doc.to_dict() if doc.exists else None

    def get_or_create_user(self, user_id: str) -> dict:
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_or_create_user(user_id)

        doc_ref = self._db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()

        user = {
            "userId": user_id,
            "createdAt": datetime.utcnow().isoformat(),
            "documents": []
        }
        doc_ref.set(user)
        return user

    # Document operations
    def save_document(self, document: dict) -> str:
        self._ensure_initialized()
        if self._storage:
            return self._storage.save_document(document)

        doc_id = document["documentId"]
        self._db.collection('documents').document(doc_id).set(document)

        # Update user's document list
        user_ref = self._db.collection('users').document(document["userId"])
        from firebase_admin import firestore
        user_ref.update({
            "documents": firestore.ArrayUnion([doc_id])
        })
        return doc_id

    def get_document(self, document_id: str) -> Optional[dict]:
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_document(document_id)
        doc = self._db.collection('documents').document(document_id).get()
        return doc.to_dict() if doc.exists else None

    def get_user_documents(self, user_id: str) -> List[dict]:
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_user_documents(user_id)

        docs = self._db.collection('documents').where('userId', '==', user_id).get()
        return [doc.to_dict() for doc in docs]

    def delete_document(self, document_id: str) -> bool:
        self._ensure_initialized()
        if self._storage:
            return self._storage.delete_document(document_id)

        doc = self.get_document(document_id)
        if doc is None:
            return False

        # Delete threads
        threads = self._db.collection('threads').where('documentId', '==', document_id).get()
        for thread in threads:
            thread.reference.delete()

        # Remove from user's list
        from firebase_admin import firestore
        user_ref = self._db.collection('users').document(doc["userId"])
        user_ref.update({
            "documents": firestore.ArrayRemove([document_id])
        })

        # Delete document
        self._db.collection('documents').document(document_id).delete()
        return True

    # Thread operations
    def save_thread(self, thread: dict) -> str:
        self._ensure_initialized()
        if self._storage:
            return self._storage.save_thread(thread)

        thread_id = thread["threadId"]
        self._db.collection('threads').document(thread_id).set(thread)
        return thread_id

    def get_thread(self, thread_id: str) -> Optional[dict]:
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_thread(thread_id)
        doc = self._db.collection('threads').document(thread_id).get()
        return doc.to_dict() if doc.exists else None

    def get_document_threads(self, document_id: str) -> List[dict]:
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_document_threads(document_id)

        docs = self._db.collection('threads').where('documentId', '==', document_id).get()
        return [doc.to_dict() for doc in docs]

    def add_message_to_thread(self, thread_id: str, message: dict) -> bool:
        self._ensure_initialized()
        if self._storage:
            return self._storage.add_message_to_thread(thread_id, message)

        from firebase_admin import firestore
        thread_ref = self._db.collection('threads').document(thread_id)
        thread_ref.update({
            "messages": firestore.ArrayUnion([message]),
            "updatedAt": datetime.utcnow().isoformat()
        })
        return True

    # Storage operations (PDF upload)
    def upload_pdf(self, document_id: str, pdf_content: bytes) -> Optional[str]:
        """Upload PDF to Firebase Storage and return the URL."""
        self._ensure_initialized()
        if self._storage or self._bucket is None:
            # In-memory mode: no file storage
            return None

        blob = self._bucket.blob(f"pdfs/{document_id}.pdf")
        blob.upload_from_string(pdf_content, content_type='application/pdf')
        blob.make_public()
        return blob.public_url

    # Memory operations
    def get_agent_memory(self, document_id: str, agent_id: str) -> Optional[dict]:
        """Get agent memory for a document."""
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_agent_memory(document_id, agent_id)

        doc = self._db.collection('memories').document(f"{document_id}_{agent_id}").get()
        return doc.to_dict() if doc.exists else None

    def save_agent_memory(self, memory: dict) -> str:
        """Save agent memory."""
        self._ensure_initialized()
        if self._storage:
            return self._storage.save_agent_memory(memory)

        document_id = memory["documentId"]
        agent_id = memory["agentId"]
        key = f"{document_id}_{agent_id}"
        self._db.collection('memories').document(key).set(memory)
        return key

    def delete_document_memories(self, document_id: str) -> int:
        """Delete all memories for a document."""
        self._ensure_initialized()
        if self._storage:
            return self._storage.delete_document_memories(document_id)

        memories = self._db.collection('memories').where('documentId', '==', document_id).get()
        count = 0
        for mem in memories:
            mem.reference.delete()
            count += 1
        return count

    def get_document_memories(self, document_id: str) -> List[dict]:
        """Get all agent memories for a document."""
        self._ensure_initialized()
        if self._storage:
            return self._storage.get_document_memories(document_id)

        memories = self._db.collection('memories').where('documentId', '==', document_id).get()
        return [mem.to_dict() for mem in memories]


# Singleton instance
firebase_service = FirebaseService()
