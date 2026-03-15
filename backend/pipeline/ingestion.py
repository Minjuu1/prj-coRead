"""
Grobid 기반 PDF 파싱 파이프라인

Grobid REST API 호출 → TEI XML 파싱 → Chunk 리스트 반환
좌표: PyMuPDF로 청크 텍스트를 PDF에서 직접 검색해서 추출
Grobid 미실행 시 fallback: pypdf로 텍스트만 추출 (좌표 없음)
"""
import uuid
import logging
import xml.etree.ElementTree as ET
from typing import List, Optional
import requests

logger = logging.getLogger(__name__)

GROBID_URL = "http://localhost:8070"
TEI_NS = "{http://www.tei-c.org/ns/1.0}"
MIN_CHUNK_LEN = 80  # 너무 짧은 문단 스킵


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def run_ingestion(paper_id: str, pdf_path: str):
    """
    PDF → (chunk 리스트, 논문 메타데이터 dict).
    Grobid 사용 가능하면 텍스트+구조 추출, 좌표는 PyMuPDF로 보강.
    Grobid 미실행 시 fallback: pypdf (좌표 없음).
    """
    tei_xml = _call_grobid(pdf_path)
    if tei_xml:
        logger.info(f"[ingestion] Grobid OK — parsing TEI XML for {paper_id}")
        chunks = _parse_tei(paper_id, tei_xml)
        chunks = _enrich_rects(chunks, pdf_path)
        metadata = _extract_metadata(tei_xml)
        return chunks, metadata
    else:
        logger.warning(f"[ingestion] Grobid unavailable — fallback for {paper_id}")
        return _fallback_pypdf(paper_id, pdf_path), {"title": "", "authors": [], "abstract": ""}


# ──────────────────────────────────────────────
# Grobid
# ──────────────────────────────────────────────

def _call_grobid(pdf_path: str) -> Optional[str]:
    try:
        with open(pdf_path, "rb") as f:
            r = requests.post(
                f"{GROBID_URL}/api/processFulltextDocument",
                files={"input": ("paper.pdf", f, "application/pdf")},
                data={"generateIDs": "1", "consolidateHeader": "1"},
                timeout=120,
            )
        if r.status_code == 200:
            return r.text
        logger.warning(f"[grobid] HTTP {r.status_code}")
        return None
    except Exception as e:
        logger.warning(f"[grobid] connection error: {e}")
        return None


def _parse_tei(paper_id: str, tei_xml: str) -> List[dict]:
    try:
        root = ET.fromstring(tei_xml)
    except ET.ParseError as e:
        logger.error(f"[grobid] XML parse error: {e}")
        return []

    body = root.find(f".//{TEI_NS}body")
    if body is None:
        return []

    divs = list(body.findall(f"{TEI_NS}div"))
    total_divs = max(len(divs), 1)
    chunks: List[dict] = []
    char_offset = 0

    for sec_idx, div in enumerate(divs):
        head = div.find(f"{TEI_NS}head")
        section_title = _elem_text(head) if head is not None else "Unknown"

        paragraphs = list(div.findall(f"{TEI_NS}p"))
        for p in paragraphs:
            text = _elem_text(p)
            if not text or len(text) < MIN_CHUNK_LEN:
                continue

            chunk = {
                "id": str(uuid.uuid4()),
                "paperId": paper_id,
                "content": text,
                "section": section_title,
                "position": round(sec_idx / total_divs, 4),
                "charStart": char_offset,
                "charEnd": char_offset + len(text),
                "pageStart": 1,
                "pageEnd": 1,
                "rects": [],
                "linkedChunks": [],
            }
            chunks.append(chunk)
            char_offset += len(text) + 1

    logger.info(f"[grobid] extracted {len(chunks)} chunks")
    return chunks


# ──────────────────────────────────────────────
# PyMuPDF 좌표 보강
# ──────────────────────────────────────────────

def _normalize(s: str) -> str:
    """비교용 텍스트 정규화: 소문자 + 공백 압축."""
    import re
    return re.sub(r"\s+", " ", s.lower()).strip()


def _enrich_rects(chunks: List[dict], pdf_path: str) -> List[dict]:
    """
    PyMuPDF get_text("dict")로 라인 단위 bbox 추출.
    청크 prefix/suffix로 시작 라인과 끝 라인을 찾아 라인별 rect 반환.
    """
    try:
        import fitz
    except ImportError:
        logger.warning("[enrich] pymupdf not installed — no coordinates")
        return chunks

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.warning(f"[enrich] cannot open PDF: {e}")
        return chunks

    # 페이지별 라인 목록 사전 계산
    # lines: [(x0, y0, x1, y1, normalized_text), ...]
    page_lines: dict = {}
    page_dims: dict = {}
    for i, page in enumerate(doc):
        pn = i + 1
        page_dims[pn] = (page.rect.width, page.rect.height)
        lines = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                line_text = " ".join(sp["text"] for sp in line["spans"])
                bbox = line["bbox"]
                lines.append((bbox[0], bbox[1], bbox[2], bbox[3], _normalize(line_text)))
        page_lines[pn] = lines

    for chunk in chunks:
        raw = chunk["content"]
        norm = _normalize(raw)
        if not norm:
            continue

        prefix = norm[:35]   # 시작 탐색용
        suffix = norm[-35:]  # 끝 탐색용

        found = False
        for page_num, lines in page_lines.items():
            pw, ph = page_dims[page_num]

            # 시작 라인: prefix의 앞 20자가 라인 텍스트에 포함되는 첫 라인
            start_idx = None
            for idx, (x0, y0, x1, y1, lt) in enumerate(lines):
                if prefix[:20] in lt:
                    start_idx = idx
                    break
            if start_idx is None:
                continue

            # 끝 라인: 누적 텍스트 길이가 청크 길이에 도달할 때까지 라인 추가
            target_len = len(norm)
            accumulated = 0
            end_idx = start_idx
            for idx in range(start_idx, min(start_idx + 60, len(lines))):
                accumulated += len(lines[idx][4]) + 1
                end_idx = idx
                if accumulated >= target_len * 0.85:
                    break

            # 각 라인 → rect
            rects = []
            for idx in range(start_idx, end_idx + 1):
                x0, y0, x1, y1, _ = lines[idx]
                rects.append({
                    "page": page_num,
                    "x1": round(x0, 4),
                    "y1": round(y0, 4),
                    "x2": round(x1, 4),
                    "y2": round(y1, 4),
                    "width": round(pw, 2),
                    "height": round(ph, 2),
                })

            if rects:
                chunk["rects"] = rects
                chunk["pageStart"] = page_num
                chunk["pageEnd"] = page_num
                found = True
                break

        if not found:
            logger.debug(f"[enrich] no match: {prefix[:25]!r}")

    doc.close()
    found_count = sum(1 for c in chunks if c["rects"])
    logger.warning(f"[enrich] coords found for {found_count}/{len(chunks)} chunks")
    return chunks


# ──────────────────────────────────────────────
# Metadata extraction from TEI header
# ──────────────────────────────────────────────

def _extract_metadata(tei_xml: str) -> dict:
    """TEI XML header에서 제목·저자·초록 추출."""
    try:
        root = ET.fromstring(tei_xml)
    except ET.ParseError:
        return {"title": "", "authors": [], "abstract": ""}

    # Title
    title_elem = root.find(f".//{TEI_NS}titleStmt/{TEI_NS}title")
    title = _elem_text(title_elem) if title_elem is not None else ""

    # Authors: header의 analytic/author 또는 titleStmt/author 아래 persName만 추출
    # (references 섹션의 citation 저자 제외)
    authors = []
    header = root.find(f".//{TEI_NS}teiHeader")
    author_scope = []
    if header is not None:
        # processFulltextDocument: fileDesc/sourceDesc/biblStruct/analytic/author
        for author in header.findall(f".//{TEI_NS}analytic/{TEI_NS}author"):
            author_scope.append(author)
        # fallback: titleStmt/author
        if not author_scope:
            for author in header.findall(f".//{TEI_NS}titleStmt/{TEI_NS}author"):
                author_scope.append(author)
    for author in author_scope:
        persName = author.find(f"{TEI_NS}persName")
        if persName is None:
            continue
        forename = _elem_text(persName.find(f"{TEI_NS}forename")) if persName.find(f"{TEI_NS}forename") is not None else ""
        surname = _elem_text(persName.find(f"{TEI_NS}surname")) if persName.find(f"{TEI_NS}surname") is not None else ""
        name = " ".join(filter(None, [forename, surname]))
        if name:
            authors.append(name)

    # Abstract: profileDesc/abstract 내 p 텍스트 합치기
    abstract_parts = []
    abstract_elem = root.find(f".//{TEI_NS}abstract")
    if abstract_elem is not None:
        for p in abstract_elem.iter(f"{TEI_NS}p"):
            text = _elem_text(p)
            if text:
                abstract_parts.append(text)
    abstract = " ".join(abstract_parts)

    return {"title": title, "authors": authors, "abstract": abstract}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _elem_text(elem: ET.Element) -> str:
    return "".join(elem.itertext()).strip()


# ──────────────────────────────────────────────
# Fallback: pypdf (좌표 없음)
# ──────────────────────────────────────────────

def _fallback_pypdf(paper_id: str, pdf_path: str) -> List[dict]:
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("[fallback] pypdf not installed")
        return []

    reader = PdfReader(pdf_path)
    chunks = []
    char_offset = 0

    for page_num, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text or len(text) < MIN_CHUNK_LEN:
            continue

        chunk = {
            "id": str(uuid.uuid4()),
            "paperId": paper_id,
            "content": text,
            "section": f"Page {page_num}",
            "position": round((page_num - 1) / max(len(reader.pages), 1), 4),
            "charStart": char_offset,
            "charEnd": char_offset + len(text),
            "pageStart": page_num,
            "pageEnd": page_num,
            "rects": [],
            "linkedChunks": [],
        }
        chunks.append(chunk)
        char_offset += len(text) + 1

    logger.info(f"[fallback] extracted {len(chunks)} page-level chunks")
    return chunks
