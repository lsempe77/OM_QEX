"""
TEI XML Parser for GROBID Outputs
Adapted from paper-screening-pipeline for data extraction use case.
"""

from lxml import etree
from pathlib import Path
from typing import Dict, Optional, List


class TEIParser:
    """Parse GROBID TEI XML files to extract full text and metadata."""
    
    # TEI namespace
    NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    def __init__(self, tei_file: Path):
        """Initialize parser with TEI XML file path."""
        self.tei_file = Path(tei_file)
        self.tree = None
        self.root = None
        self._parse()
    
    def _parse(self):
        """Parse the TEI XML file."""
        try:
            self.tree = etree.parse(str(self.tei_file))
            self.root = self.tree.getroot()
        except Exception as e:
            raise ValueError(f"Failed to parse TEI file {self.tei_file}: {e}")
    
    def get_title(self) -> str:
        """Extract paper title."""
        title_elem = self.root.find('.//tei:titleStmt/tei:title[@type="main"]', self.NS)
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()
        return ""
    
    def get_authors(self) -> List[Dict[str, str]]:
        """Extract author information."""
        authors = []
        author_elems = self.root.findall('.//tei:sourceDesc//tei:author', self.NS)
        
        for author_elem in author_elems:
            author = {}
            
            # First name
            forename = author_elem.find('.//tei:forename[@type="first"]', self.NS)
            if forename is not None and forename.text:
                author['first_name'] = forename.text.strip()
            
            # Last name
            surname = author_elem.find('.//tei:surname', self.NS)
            if surname is not None and surname.text:
                author['last_name'] = surname.text.strip()
            
            # Full name
            if 'first_name' in author and 'last_name' in author:
                author['full_name'] = f"{author['first_name']} {author['last_name']}"
            
            if author:
                authors.append(author)
        
        return authors
    
    def get_abstract(self) -> str:
        """Extract abstract text."""
        abstract_elem = self.root.find('.//tei:abstract', self.NS)
        if abstract_elem is not None:
            # Get all text, joining paragraphs
            paras = abstract_elem.findall('.//tei:p', self.NS)
            if paras:
                return ' '.join([p.text.strip() for p in paras if p.text])
            elif abstract_elem.text:
                return abstract_elem.text.strip()
        return ""
    
    def get_body_text(self) -> str:
        """Extract full body text."""
        body_elem = self.root.find('.//tei:body', self.NS)
        if body_elem is None:
            return ""
        
        # Get all text from body, preserving structure
        text_parts = []
        
        # Process all divs and paragraphs
        for elem in body_elem.iter():
            if elem.tag.endswith('p') or elem.tag.endswith('head'):
                if elem.text:
                    text_parts.append(elem.text.strip())
        
        return '\n\n'.join(text_parts)
    
    def get_full_text(self, include_abstract: bool = True) -> str:
        """Get complete paper text (abstract + body)."""
        parts = []
        
        if include_abstract:
            abstract = self.get_abstract()
            if abstract:
                parts.append(f"ABSTRACT:\n{abstract}")
        
        body = self.get_body_text()
        if body:
            parts.append(f"FULL TEXT:\n{body}")
        
        return '\n\n'.join(parts)
    
    def get_publication_year(self) -> Optional[str]:
        """Extract publication year."""
        # Try biblStruct date
        date_elem = self.root.find('.//tei:sourceDesc//tei:biblStruct//tei:date[@type="published"]', self.NS)
        if date_elem is not None:
            year = date_elem.get('when')
            if year:
                return year[:4]  # Extract year from date
        return None
    
    def get_references(self) -> List[Dict[str, str]]:
        """Extract bibliography references."""
        references = []
        ref_elems = self.root.findall('.//tei:listBibl/tei:biblStruct', self.NS)
        
        for ref_elem in ref_elems:
            ref = {}
            
            # Title
            title_elem = ref_elem.find('.//tei:title[@level="a"]', self.NS)
            if title_elem is not None and title_elem.text:
                ref['title'] = title_elem.text.strip()
            
            # Authors
            author_elems = ref_elem.findall('.//tei:author', self.NS)
            if author_elems:
                ref['authors'] = []
                for author in author_elems:
                    surname = author.find('.//tei:surname', self.NS)
                    if surname is not None and surname.text:
                        ref['authors'].append(surname.text.strip())
            
            # Year
            date_elem = ref_elem.find('.//tei:date', self.NS)
            if date_elem is not None:
                year = date_elem.get('when')
                if year:
                    ref['year'] = year[:4]
            
            if ref:
                references.append(ref)
        
        return references
    
    def get_metadata(self) -> Dict:
        """Extract all metadata in structured format."""
        return {
            'title': self.get_title(),
            'authors': self.get_authors(),
            'year': self.get_publication_year(),
            'abstract': self.get_abstract(),
            'reference_count': len(self.get_references())
        }
    
    def to_dict(self) -> Dict:
        """Convert entire document to dictionary format."""
        return {
            'metadata': self.get_metadata(),
            'full_text': self.get_full_text(),
            'references': self.get_references()
        }


def parse_tei_file(tei_file: Path) -> TEIParser:
    """Convenience function to parse a TEI file."""
    return TEIParser(tei_file)


if __name__ == "__main__":
    # Test the parser
    import sys
    
    if len(sys.argv) > 1:
        tei_path = Path(sys.argv[1])
        if tei_path.exists():
            parser = TEIParser(tei_path)
            print("Title:", parser.get_title())
            print("Authors:", parser.get_authors())
            print("Year:", parser.get_publication_year())
            print("\nAbstract:", parser.get_abstract()[:200], "...")
            print("\nBody length:", len(parser.get_body_text()), "chars")
        else:
            print(f"File not found: {tei_path}")
    else:
        print("Usage: python tei_parser.py <path_to_tei_file>")
