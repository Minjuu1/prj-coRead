import httpx
import xml.etree.ElementTree as ET
from typing import List, Optional
from dataclasses import dataclass, field
import os
import re


@dataclass
class ParsedSection:
    section_id: str
    title: str
    content: str
    order: int
    subsections: List[str] = field(default_factory=list)  # Subsection titles for reference


class PDFParserService:
    """Service for parsing PDF files using GROBID."""

    # Patterns to filter out non-content sections
    FIGURE_PATTERN = re.compile(r'^(Figure|Fig\.?|Table|Appendix)\s*\d*', re.IGNORECASE)

    # Minimum content length to be considered a valid section
    MIN_CONTENT_LENGTH = 100

    # Major section titles (case-insensitive) - these start new sections
    MAJOR_SECTIONS = {
        'abstract', 'introduction', 'background', 'related work', 'related works',
        'literature review', 'methods', 'method', 'methodology', 'study design',
        'materials and methods', 'results', 'findings', 'analysis',
        'discussion', 'conclusion', 'conclusions', 'summary', 'future work',
        'acknowledgments', 'acknowledgements', 'references'
    }

    # Sections that should be merged into the previous major section
    SUBSECTION_PATTERNS = [
        r'^experimental',  # Experimental Task, Experimental Treatments, etc.
        r'^rq\d',  # RQ1, RQ2, etc.
        r'^\d+\.\d+',  # 2.1, 3.2, etc.
        r'^participants?$',
        r'^procedure$',
        r'^measurements?$',
        r'^data\s+(collection|analysis)',
    ]

    def __init__(self, grobid_url: Optional[str] = None):
        self.grobid_url = grobid_url or os.getenv("GROBID_URL", "http://localhost:8070")

    async def check_health(self) -> bool:
        """Check if GROBID service is available."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.grobid_url}/api/isalive")
                return response.status_code == 200
        except Exception:
            return False

    async def parse_pdf(self, pdf_content: bytes) -> dict:
        """
        Parse PDF content using GROBID and extract sections.

        Args:
            pdf_content: Raw PDF file bytes

        Returns:
            dict with 'title' and 'sections' keys
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.grobid_url}/api/processFulltextDocument",
                files={"input": ("document.pdf", pdf_content, "application/pdf")},
                data={
                    "consolidateHeader": "1",
                    "consolidateCitations": "0",
                    "includeRawCitations": "0",
                    "includeRawAffiliations": "0",
                    "teiCoordinates": "0",
                    "segmentSentences": "1",
                }
            )

            if response.status_code != 200:
                raise Exception(f"GROBID parsing failed: {response.status_code}")

            tei_xml = response.text
            return self._parse_tei_xml(tei_xml)

    def _parse_tei_xml(self, tei_xml: str) -> dict:
        """Parse TEI XML output from GROBID."""
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        root = ET.fromstring(tei_xml)

        # Extract title
        title_elem = root.find('.//tei:titleStmt/tei:title', ns)
        title = title_elem.text if title_elem is not None and title_elem.text else "Untitled Document"

        sections: List[ParsedSection] = []
        order = 0

        # Extract abstract
        abstract_elem = root.find('.//tei:profileDesc/tei:abstract', ns)
        if abstract_elem is not None:
            abstract_text = self._extract_all_text(abstract_elem, ns)
            if abstract_text.strip() and len(abstract_text.strip()) >= self.MIN_CONTENT_LENGTH:
                sections.append(ParsedSection(
                    section_id=f"section_{order}",
                    title="Abstract",
                    content=abstract_text.strip(),
                    order=order
                ))
                order += 1

        # Extract body sections - only TOP-LEVEL divs
        body = root.find('.//tei:body', ns)
        if body is not None:
            # Only get direct children divs, not nested ones
            for div in body.findall('tei:div', ns):
                section = self._extract_section_with_subsections(div, ns, order)

                if section and self._is_valid_section(section):
                    sections.append(section)
                    order += 1

        # Post-process: merge orphan sections and clean up
        sections = self._post_process_sections(sections)

        # If no sections found, try to get all text as one section
        if not sections:
            all_text = self._extract_all_text(root, ns)
            if all_text.strip():
                sections.append(ParsedSection(
                    section_id="section_0",
                    title="Content",
                    content=all_text.strip(),
                    order=0
                ))

        return {
            "title": title,
            "sections": [
                {
                    "sectionId": s.section_id,
                    "title": s.title,
                    "content": s.content,
                    "order": s.order,
                    "subsections": s.subsections,
                }
                for s in sections
            ]
        }

    def _extract_section_with_subsections(self, div, ns, order: int) -> Optional[ParsedSection]:
        """
        Extract a section including all its nested subsections.
        Subsection content is merged into the parent section.
        """
        # Get section title
        head = div.find('tei:head', ns)
        section_title = ""
        if head is not None and head.text:
            section_title = head.text.strip()
            # Clean up numbering like "2.1" from title
            section_title = re.sub(r'^\d+(\.\d+)*\s*', '', section_title).strip()

        if not section_title:
            section_title = f"Section {order + 1}"

        # Collect all paragraphs from this div and nested divs
        all_paragraphs = []
        subsection_titles = []

        self._collect_content_recursive(div, ns, all_paragraphs, subsection_titles)

        if not all_paragraphs:
            return None

        content = "\n\n".join(all_paragraphs)

        return ParsedSection(
            section_id=f"section_{order}",
            title=section_title,
            content=content,
            order=order,
            subsections=subsection_titles
        )

    def _collect_content_recursive(self, element, ns, paragraphs: List[str], subsection_titles: List[str]):
        """Recursively collect paragraphs and track subsection titles."""
        # Get paragraphs at this level
        for p in element.findall('tei:p', ns):
            p_text = self._extract_all_text(p, ns)
            if p_text.strip():
                paragraphs.append(p_text.strip())

        # Process nested divs (subsections)
        for nested_div in element.findall('tei:div', ns):
            # Track subsection title
            nested_head = nested_div.find('tei:head', ns)
            if nested_head is not None and nested_head.text:
                subsection_title = nested_head.text.strip()
                subsection_title = re.sub(r'^\d+(\.\d+)*\s*', '', subsection_title).strip()
                if subsection_title:
                    subsection_titles.append(subsection_title)
                    # Add subsection title as a paragraph header
                    paragraphs.append(f"### {subsection_title}")

            # Recursively collect content from nested div
            self._collect_content_recursive(nested_div, ns, paragraphs, subsection_titles)

    def _is_valid_section(self, section: ParsedSection) -> bool:
        """Check if a section should be included."""
        # Filter out Figure/Table captions
        if self.FIGURE_PATTERN.match(section.title):
            return False

        # Filter out sections with only figure references
        if section.title.startswith("Section ") and len(section.content) < self.MIN_CONTENT_LENGTH:
            return False

        # Filter out very short content
        if len(section.content) < self.MIN_CONTENT_LENGTH:
            return False

        return True

    def _post_process_sections(self, sections: List[ParsedSection]) -> List[ParsedSection]:
        """Post-process sections to clean up and merge non-major sections."""
        if not sections:
            return sections

        processed = []

        for section in sections:
            # Clean up section title
            section.title = self._clean_title(section.title)

            # Check if this is a major section
            is_major = self._is_major_section(section.title)

            # Skip sections that are just "Section N" with short content
            if section.title.startswith("Section ") and len(section.content) < 200:
                if processed:
                    processed[-1].content += "\n\n" + section.content
                continue

            if is_major:
                # Start a new major section
                processed.append(section)
            else:
                # Merge into previous section if exists
                if processed:
                    # Add as subsection content with header
                    processed[-1].content += f"\n\n### {section.title}\n\n{section.content}"
                    processed[-1].subsections.append(section.title)
                else:
                    # No previous section, keep as is
                    processed.append(section)

        # Re-number sections
        for i, section in enumerate(processed):
            section.section_id = f"section_{i}"
            section.order = i

        return processed

    def _is_major_section(self, title: str) -> bool:
        """Check if a title represents a major section."""
        # Normalize title for comparison
        normalized = title.lower().strip()

        # First check if it matches subsection patterns (these are NOT major)
        for pattern in self.SUBSECTION_PATTERNS:
            if re.match(pattern, normalized, re.IGNORECASE):
                return False

        # Remove leading numbers and punctuation
        clean_title = re.sub(r'^[\d\.\s]+', '', normalized)

        # Check exact match with major sections
        if clean_title in self.MAJOR_SECTIONS:
            return True

        # Check if title starts with a major section name
        for major in self.MAJOR_SECTIONS:
            if clean_title.startswith(major):
                return True

        return False

    def _clean_title(self, title: str) -> str:
        """Clean up section title."""
        # Remove leading/trailing whitespace
        title = title.strip()

        # Remove leading numbers like "1.", "2.1", etc.
        title = re.sub(r'^\d+(\.\d+)*\.?\s*', '', title)

        # Check if title contains a subsection number pattern (e.g., "RELATED WORK 2.1 Subsection")
        # If so, extract just the main section name
        match = re.match(r'^([A-Z\s]+?)\s+\d+\.\d+', title)
        if match:
            # Return just the main section name (e.g., "RELATED WORK")
            title = match.group(1).strip()

        # Capitalize first letter
        if title and title[0].islower():
            title = title[0].upper() + title[1:]

        return title

    def _extract_all_text(self, element, ns) -> str:
        """Extract all text from an XML element, including nested elements."""
        texts = []

        if element.text:
            texts.append(element.text)

        for child in element:
            child_text = self._extract_all_text(child, ns)
            if child_text:
                texts.append(child_text)
            if child.tail:
                texts.append(child.tail)

        return " ".join(texts)


# Singleton instance
pdf_parser_service = PDFParserService()
