"""
Firebase Storage — PDF 업로드/다운로드.

Firebase app은 firestore.py의 _get_db()가 먼저 호출되어 초기화된 상태를 가정.
Storage bucket 이름은 FIREBASE_STORAGE_BUCKET 환경변수에서 읽음.
"""
import os
import logging

logger = logging.getLogger(__name__)

_bucket = None
_available: bool | None = None  # None = not checked yet


def _get_bucket():
    global _bucket, _available
    if _available is False:
        return None
    if _bucket is not None:
        return _bucket
    try:
        import firebase_admin
        from firebase_admin import credentials, storage

        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        if not bucket_name:
            logger.warning("[storage] FIREBASE_STORAGE_BUCKET not set — storage disabled")
            _available = False
            return None

        cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "firebase-credentials.json")
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
        elif "storageBucket" not in firebase_admin.get_app().options:
            # App already initialized without storageBucket — re-init not possible,
            # so pass bucket name directly to storage.bucket()
            pass

        _bucket = storage.bucket(bucket_name)
        _available = True
        logger.info(f"[storage] connected to bucket: {bucket_name}")
        return _bucket
    except Exception as e:
        logger.warning(f"[storage] init failed ({e}) — storage disabled")
        _available = False
        return None


def is_available() -> bool:
    return _get_bucket() is not None


def upload_pdf(paper_id: str, contents: bytes) -> str | None:
    """PDF bytes를 Storage에 업로드하고 gs:// path를 반환. 실패 시 None."""
    bucket = _get_bucket()
    if bucket is None:
        return None
    try:
        blob = bucket.blob(f"papers/{paper_id}.pdf")
        blob.upload_from_string(contents, content_type="application/pdf")
        logger.info(f"[storage] uploaded papers/{paper_id}.pdf")
        return f"gs://{bucket.name}/papers/{paper_id}.pdf"
    except Exception as e:
        logger.warning(f"[storage] upload failed for {paper_id}: {e}")
        return None


def download_pdf(paper_id: str) -> bytes | None:
    """Storage에서 PDF bytes를 다운로드. 실패 시 None."""
    bucket = _get_bucket()
    if bucket is None:
        return None
    try:
        blob = bucket.blob(f"papers/{paper_id}.pdf")
        data = blob.download_as_bytes()
        logger.info(f"[storage] downloaded papers/{paper_id}.pdf ({len(data)} bytes)")
        return data
    except Exception as e:
        logger.warning(f"[storage] download failed for {paper_id}: {e}")
        return None
