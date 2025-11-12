"""
PDF Annotation App for 4-Phase Extraction Validation

This Streamlit app allows reviewers to:
1. View PDFs alongside extracted outcomes from all 4 phases
2. Compare extraction methods (JSON/TEI/PDF vision)
3. Annotate outcomes as correct/incorrect/missing
4. Add comments and corrections
5. Export annotations for analysis

Usage:
    streamlit run pdf_annotation_app.py
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import base64
from typing import Dict, List, Optional

# PDF viewer
try:
    from streamlit_pdf_viewer import pdf_viewer
    PDF_VIEWER_AVAILABLE = True
except ImportError:
    PDF_VIEWER_AVAILABLE = False
    st.sidebar.warning("streamlit-pdf-viewer not installed. Using fallback display.")

# Page config
st.set_page_config(
    page_title="Outcome Mapping Validation",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths - use absolute paths to avoid working directory issues
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # OM_QEX directory
PDFS_DIR = PROJECT_ROOT / "data" / "pdfs"
EXTRACTIONS_DIR = Path(__file__).resolve().parent / "outputs" / "twopass_extractions" / "json"
EXTRACTIONS_CSV = Path(__file__).resolve().parent / "outputs" / "twopass_extractions" / "extracted_data.csv"
ANNOTATIONS_FILE = Path(__file__).resolve().parent / "outputs" / "twopass_annotations.json"
HUMAN_OM_FILE = PROJECT_ROOT / "data" / "human_extraction" / "OM_human_extraction.csv"
MASTER_CSV = PROJECT_ROOT / "data" / "raw" / "Master file of included studies (n=114) 11 Nov(data).csv"

# Validation papers
VALIDATION_PAPERS = {
    'HUHR5QHM': {'id': '121357881', 'name': 'Diamouténé (2024)', 'human_outcomes': 1},
    'PHRKN65M': {'id': '121294984', 'name': 'Burchi (2018)', 'human_outcomes': 9},
    '6WTBIFX2': {'id': '121294795', 'name': 'Matsuda (2024)', 'human_outcomes': 4},
    'UBFBIAVN': {'id': '121058363', 'name': 'Burchi (2021)', 'human_outcomes': 1},
    '55XQSDKK': {'id': '121058368', 'name': 'Banerjee (2017)', 'human_outcomes': 1},
    'ABM3E3ZP': {'id': '121058364', 'name': 'Maldonado (2019)', 'human_outcomes': 2},
    'V5P2S7S3': {'id': '121326829', 'name': 'Zheng (2023)', 'human_outcomes': 15},
    'K2ZJ4QNZ': {'id': '121328483', 'name': 'Banerjee (2022)', 'human_outcomes': 1},
    '949EZS93': {'id': '121315117', 'name': 'Carpio (2016)', 'human_outcomes': 2},
    'DXHZBI2X': {'id': '121319138', 'name': 'Carpio (2012)', 'human_outcomes': 1},
    '9BUBMDBG': {'id': '121307773', 'name': 'Macours (2013)', 'human_outcomes': 14},
    '36VWQDDT': {'id': '121327988', 'name': 'Correa (2021)', 'human_outcomes': 1},
    'XWDVG8KS': {'id': '121498842', 'name': 'Mahecha', 'human_outcomes': 9},
    'HWR58RZK': {'id': '122182711', 'name': 'Study HWR58RZK', 'human_outcomes': 1},
    'CG73D75P': {'id': '122182713', 'name': 'IPA (2022)', 'human_outcomes': 1},
}


def load_paper_titles() -> Dict[str, str]:
    """Load full paper titles from master CSV."""
    try:
        if not MASTER_CSV.exists():
            return {}
        
        df = pd.read_csv(MASTER_CSV)
        titles = {}
        
        for key, info in VALIDATION_PAPERS.items():
            study_id = info['id']
            match = df[df['ID'].astype(str) == study_id]
            
            if len(match) > 0:
                title = match['Title'].values[0]
                if pd.notna(title):
                    titles[key] = str(title)
        
        return titles
    except Exception as e:
        st.sidebar.warning(f"Could not load paper titles: {e}")
        return {}


def load_pdf_base64(pdf_path: Path) -> str:
    """Load PDF and convert to base64 for embedding."""
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    return base64.b64encode(pdf_bytes).decode('utf-8')


def display_pdf(pdf_path: Path):
    """Display PDF with streamlit-pdf-viewer or fallback options."""
    try:
        # Offer download button first
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**PDF Viewer**")
        with col2:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=pdf_path.name,
                mime="application/pdf",
                use_container_width=True
            )
        
        # Use streamlit-pdf-viewer if available (better compatibility)
        if PDF_VIEWER_AVAILABLE:
            pdf_viewer(pdf_bytes, height=800)
        else:
            # Fallback to iframe display
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Add a notice about browser compatibility
            st.info("💡 **PDF not displaying?** Use the download button above to view in your PDF reader, or try a different browser (Chrome/Edge work best).")
            
            pdf_display = f'''
                <iframe 
                    src="data:application/pdf;base64,{pdf_base64}" 
                    width="100%" 
                    height="800" 
                    type="application/pdf"
                    style="border: 1px solid #ccc;">
                    <p>Your browser does not support embedded PDFs. Please use the download button above.</p>
                </iframe>
            '''
            st.markdown(pdf_display, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error loading PDF: {e}")
        st.info("Please use the download button to view the PDF separately.")


def load_extraction(key: str) -> Optional[Dict]:
    """Load LLM extraction JSON for a paper."""
    json_file = EXTRACTIONS_DIR / f"{key}.json"
    if not json_file.exists():
        return None
    
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_human_outcomes(study_id: str) -> pd.DataFrame:
    """Load human-coded outcomes for a study."""
    if not HUMAN_OM_FILE.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(HUMAN_OM_FILE)
    df['study_id_base'] = df['EPPI ID'].str.split('_').str[0]
    return df[df['study_id_base'] == study_id]


def load_annotations() -> Dict:
    """Load existing annotations."""
    if ANNOTATIONS_FILE.exists():
        with open(ANNOTATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_annotations(annotations: Dict):
    """Save annotations to JSON file."""
    ANNOTATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ANNOTATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2)


def export_annotations_csv():
    """Export annotations to CSV format."""
    annotations = load_annotations()
    
    records = []
    for key, paper_annotations in annotations.items():
        for idx, outcome_ann in enumerate(paper_annotations.get('outcomes', [])):
            records.append({
                'key': key,
                'study_name': VALIDATION_PAPERS.get(key, {}).get('name', ''),
                'outcome_index': idx,
                'outcome_category': outcome_ann.get('outcome_category', ''),
                'validation_status': outcome_ann.get('status', ''),
                'comment': outcome_ann.get('comment', ''),
                'corrected_category': outcome_ann.get('corrected_category', ''),
                'annotator': outcome_ann.get('annotator', ''),
            })
    
    return pd.DataFrame(records)


def main():
    st.title("📊 Outcome Mapping Validation")
    
    # Load paper titles from master CSV
    paper_titles = load_paper_titles()
    
    # Sidebar - Paper selection
    st.sidebar.header("Select Paper")
    
    # Load all extractions to get methods
    extraction_methods = {}
    for key in VALIDATION_PAPERS.keys():
        ext = load_extraction(key)
        if ext:
            extraction_methods[key] = ext.get('extraction_method', 'unknown')
    
    # Format paper names with extraction method badges
    def format_paper_name(k):
        method = extraction_methods.get(k, 'unknown')
        method_emoji = {
            'twopass_llm': '🟢',
            'tei_fallback': '🟡', 
            'pdf_vision': '🔵',
            'unknown': '⚪'
        }
        emoji = method_emoji.get(method, '⚪')
        human_count = VALIDATION_PAPERS[k]['human_outcomes']
        return f"{emoji} {k} - {VALIDATION_PAPERS[k]['name']} ({human_count} human)"
    
    selected_key = st.sidebar.selectbox(
        "Paper",
        options=list(VALIDATION_PAPERS.keys()),
        format_func=format_paper_name
    )
    
    # Show extraction method legend
    st.sidebar.markdown("**Method Legend:**")
    st.sidebar.markdown("🟢 Two-pass JSON (Phase 1+2)")
    st.sidebar.markdown("🟡 TEI XML Fallback (Phase 3)")
    st.sidebar.markdown("🔵 PDF Vision (Phase 4)")
    
    paper_info = VALIDATION_PAPERS[selected_key]
    study_id = paper_info['id']
    
    # Load data
    pdf_path = PDFS_DIR / f"{selected_key}.pdf"
    extraction = load_extraction(selected_key)
    human_outcomes = load_human_outcomes(study_id)
    annotations = load_annotations()
    
    # Paper annotations key
    paper_ann_key = selected_key
    if paper_ann_key not in annotations:
        annotations[paper_ann_key] = {'outcomes': [], 'paper_notes': ''}
    
    # Sidebar - Annotator info
    st.sidebar.header("Annotator")
    annotator_name = st.sidebar.text_input("Your name", value="")
    
    # Sidebar - Statistics
    st.sidebar.header("Statistics")
    if extraction and 'outcomes' in extraction:
        llm_count = len(extraction['outcomes'])
        human_count = len(human_outcomes)
        st.sidebar.metric("LLM Outcomes", llm_count)
        st.sidebar.metric("Human Outcomes", human_count)
        if llm_count > 0 and human_count > 0:
            st.sidebar.metric("Ratio", f"{llm_count/human_count:.1f}x")
    
    # Sidebar - Export
    st.sidebar.header("Export")
    if st.sidebar.button("💾 Export All Annotations"):
        annotations_df = export_annotations_csv()
        if not annotations_df.empty:
            csv = annotations_df.to_csv(index=False)
            st.sidebar.download_button(
                label="Download CSV",
                data=csv,
                file_name="om_annotations.csv",
                mime="text/csv"
            )
            st.sidebar.success(f"Exported {len(annotations_df)} annotations")
        else:
            st.sidebar.warning("No annotations to export")
    
    # Main content - Two columns
    col1, col2 = st.columns([2, 1])
    
    # Left column - PDF viewer
    with col1:
        # Show full paper title if available
        if selected_key in paper_titles:
            st.subheader(f"📄 {paper_info['name']}")
            st.caption(f"_{paper_titles[selected_key]}_")
        else:
            st.subheader(f"📄 PDF: {paper_info['name']}")
        
        if not pdf_path.exists():
            st.warning(f"⚠️ PDF not found in repository")
            st.info(f"**Expected location:** `{pdf_path.name}`")
            
            # Provide helpful info for deployment
            st.markdown("""
            **For validation without embedded PDFs:**
            1. You can still review the extracted outcomes below
            2. The human outcomes show expected table/page locations
            3. Cross-reference with the paper if you have access to it
            
            **Note:** PDFs may not be available in the deployed version to reduce repository size.
            """)
            
            # Debug info (collapsible)
            with st.expander("🔍 Debug Info"):
                st.code(f"Looking for: {pdf_path.absolute()}")
                st.code(f"PDFS_DIR: {PDFS_DIR.absolute()}")
                st.write(f"PDFS_DIR exists: {PDFS_DIR.exists()}")
                if PDFS_DIR.exists():
                    available_pdfs = list(PDFS_DIR.glob("*.pdf"))
                    st.write(f"Available PDFs: {len(available_pdfs)}")
                    if available_pdfs:
                        st.write("First 5 PDFs:", [p.name for p in available_pdfs[:5]])
        else:
            display_pdf(pdf_path)
    
    # Right column - Extracted outcomes
    with col2:
        if extraction is None:
            st.error(f"Extraction not found for {selected_key}")
            return
        
        # Show extraction method at top
        extraction_method = extraction.get('extraction_method', 'unknown')
        method_display = {
            'twopass_llm': '🟢 **Two-pass JSON** (Phase 1+2)',
            'tei_fallback': '🟡 **TEI XML Fallback** (Phase 3)',
            'pdf_vision': '🔵 **PDF Vision** (Phase 4)',
            'unknown': '⚪ Unknown method'
        }
        st.markdown(f"### Extraction Method\n{method_display.get(extraction_method, '⚪ Unknown')}")
        
        # Show human outcomes first for comparison
        st.markdown("---")
        st.subheader("👤 Human Extracted Outcomes")
        
        if len(human_outcomes) > 0:
            st.markdown(f"**Count:** {len(human_outcomes)} outcomes")
            
            for human_idx, (idx, row) in enumerate(human_outcomes.iterrows(), start=1):
                outcome_cat = row.get('Outcome category \n(as described in study)', 'N/A')
                with st.expander(f"**Human {human_idx}**: {outcome_cat}", expanded=False):
                    st.markdown(f"**Category:** {outcome_cat}")
                    st.markdown(f"**Group:** {row.get('Outcome group \n(as described in protocol)', 'N/A')}")
                    
                    location = row.get('Location of data to be extracted \n(page #; table #; table label; row label; column label)', '')
                    if location and str(location) != 'nan':
                        st.markdown(f"**Location:** {location}")
                    
                    table_type = row.get('Table type', '')
                    if table_type and str(table_type) != 'nan':
                        st.markdown(f"**Table type:** {table_type}")
        else:
            st.info("No human outcomes coded for this paper")
        
        st.markdown("---")
        st.subheader("🤖 LLM Extracted Outcomes")
        
        outcomes = extraction.get('outcomes', [])
        
        if not outcomes:
            st.warning("No outcomes extracted")
            return
        
        # Show total tables and outcomes
        total_tables = extraction.get('total_tables', 0)
        st.markdown(f"**Tables found:** {total_tables} | **Outcomes:** {len(outcomes)}")
        
        # Paper-level notes
        st.markdown("---")
        paper_notes = st.text_area(
            "📝 Paper-level notes",
            value=annotations[paper_ann_key].get('paper_notes', ''),
            height=100,
            key=f"paper_notes_{selected_key}"
        )
        annotations[paper_ann_key]['paper_notes'] = paper_notes
        
        st.markdown("---")
        
        # Initialize outcome annotations if needed
        if len(annotations[paper_ann_key]['outcomes']) != len(outcomes):
            annotations[paper_ann_key]['outcomes'] = [
                {'status': 'pending', 'comment': '', 'corrected_category': '', 'annotator': ''}
                for _ in outcomes
            ]
        
        # Display each outcome for annotation
        for idx, outcome in enumerate(outcomes):
            with st.expander(f"**Outcome {idx + 1}**: {outcome.get('outcome_category', 'N/A')}", expanded=False):
                
                # Display outcome details
                st.markdown(f"**Category:** {outcome.get('outcome_category', 'N/A')}")
                st.markdown(f"**Group:** {outcome.get('outcome_group', 'N/A')}")
                
                # New fields from 4-phase extraction
                if outcome.get('_table_number'):
                    st.markdown(f"**Table:** {outcome.get('_table_number')}")
                if outcome.get('_page_number'):
                    st.markdown(f"**Page:** {outcome.get('_page_number')}")
                
                # Statistical fields
                stats = []
                if outcome.get('effect_size') is not None:
                    stats.append(f"ES: {outcome.get('effect_size')}")
                if outcome.get('standard_error') is not None:
                    stats.append(f"SE: {outcome.get('standard_error')}")
                if outcome.get('p_value') is not None:
                    stats.append(f"p: {outcome.get('p_value')}")
                if outcome.get('ci_lower') is not None and outcome.get('ci_upper') is not None:
                    stats.append(f"CI: [{outcome.get('ci_lower')}, {outcome.get('ci_upper')}]")
                if outcome.get('n_observations') is not None:
                    stats.append(f"N: {outcome.get('n_observations')}")
                
                if stats:
                    st.markdown(f"**Statistics:** {' | '.join(stats)}")
                
                if outcome.get('literal_text'):
                    st.markdown(f"**Literal text:** `{outcome.get('literal_text')}`")
                
                if outcome.get('text_position'):
                    st.markdown(f"**Position:** {outcome.get('text_position')}")
                
                st.markdown("---")
                
                # Annotation controls
                col_a, col_b = st.columns([1, 2])
                
                with col_a:
                    status = st.selectbox(
                        "Validation",
                        options=['pending', 'correct', 'incorrect', 'duplicate', 'not_outcome'],
                        index=['pending', 'correct', 'incorrect', 'duplicate', 'not_outcome'].index(
                            annotations[paper_ann_key]['outcomes'][idx].get('status', 'pending')
                        ),
                        key=f"status_{selected_key}_{idx}"
                    )
                    annotations[paper_ann_key]['outcomes'][idx]['status'] = status
                
                with col_b:
                    comment = st.text_input(
                        "Comment",
                        value=annotations[paper_ann_key]['outcomes'][idx].get('comment', ''),
                        key=f"comment_{selected_key}_{idx}"
                    )
                    annotations[paper_ann_key]['outcomes'][idx]['comment'] = comment
                
                # Correction field (if incorrect)
                if status == 'incorrect':
                    corrected = st.text_input(
                        "Corrected category name",
                        value=annotations[paper_ann_key]['outcomes'][idx].get('corrected_category', ''),
                        key=f"corrected_{selected_key}_{idx}"
                    )
                    annotations[paper_ann_key]['outcomes'][idx]['corrected_category'] = corrected
                
                # Store annotator
                annotations[paper_ann_key]['outcomes'][idx]['annotator'] = annotator_name
        
        # Save annotations button
        st.markdown("---")
        if st.button("💾 Save Annotations", type="primary"):
            save_annotations(annotations)
            st.success(f"Saved annotations for {selected_key}")
        
        # Show annotation summary
        if annotations[paper_ann_key]['outcomes']:
            st.markdown("### Annotation Summary")
            status_counts = pd.Series([
                ann['status'] for ann in annotations[paper_ann_key]['outcomes']
            ]).value_counts()
            
            col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
            col_s1.metric("Pending", status_counts.get('pending', 0))
            col_s2.metric("Correct", status_counts.get('correct', 0))
            col_s3.metric("Incorrect", status_counts.get('incorrect', 0))
            col_s4.metric("Duplicate", status_counts.get('duplicate', 0))
            col_s5.metric("Not Outcome", status_counts.get('not_outcome', 0))
        
        # Human outcomes reference
        if not human_outcomes.empty:
            st.markdown("---")
            st.markdown("### 👤 Human-Coded Outcomes (Reference)")
            
            # Get outcome category column (column 6)
            outcome_col = human_outcomes.columns[6] if len(human_outcomes.columns) > 6 else 'Outcome'
            
            for i, row in human_outcomes.iterrows():
                st.markdown(f"- {row.get(outcome_col, 'N/A')}")


if __name__ == "__main__":
    main()
