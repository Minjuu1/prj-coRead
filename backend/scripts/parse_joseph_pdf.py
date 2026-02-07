"""
Script to parse joseph.pdf and output MOCK_SECTIONS format.
Run from backend directory: python scripts/parse_joseph_pdf.py
"""
import asyncio
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_parser import pdf_parser_service


async def main():
    # Check GROBID health
    is_healthy = await pdf_parser_service.check_health()
    if not is_healthy:
        print("ERROR: GROBID is not running. Please start it first.")
        print("Run: docker run -d -p 8070:8070 grobid/grobid:0.8.0")
        return

    # Path to PDF
    pdf_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "joseph.pdf"
    )

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return

    print(f"Parsing PDF: {pdf_path}")
    print("This may take a minute...")

    # Read PDF
    with open(pdf_path, "rb") as f:
        pdf_content = f.read()

    # Parse PDF
    result = await pdf_parser_service.parse_pdf(pdf_content)

    print(f"\nTitle: {result['title']}")
    print(f"Sections found: {len(result['sections'])}")

    # Output in MOCK_SECTIONS format
    print("\n" + "="*60)
    print("MOCK_SECTIONS = [")
    for section in result['sections']:
        # Escape content for Python string
        content = section['content'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        print(f"""    {{
        "sectionId": "{section['sectionId']}",
        "title": "{section['title']}",
        "content": "{content}",
        "order": {section['order']}
    }},""")
    print("]")
    print("="*60)

    # Also save as JSON for easier use
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "joseph_sections.json"
    )
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nJSON saved to: {json_path}")

    # Print section summaries
    print("\nSection summaries:")
    for section in result['sections']:
        content_preview = section['content'][:100].replace('\n', ' ')
        print(f"  [{section['order']}] {section['title']}: {content_preview}...")


if __name__ == "__main__":
    asyncio.run(main())
