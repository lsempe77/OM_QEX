"""
Streamlit Viewer for V2 Pipeline Extraction Results

Shows extraction results from the V2 multi-phase pipeline:
- Phase 1: Table Discovery
- Phase 2: Table Filtering (RESULTS tables)
- Phase 3: TEI Extraction
- Phase 3b: PDF Vision (fallback)
- Phase 6: Final Postprocessed Results

Usage:
    streamlit run streamlit_viewer.py
"""

import streamlit as st
import json
from pathlib import Path
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Outcomes Mapping LLM validation process",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for annotations
if 'annotations' not in st.session_state:
    st.session_state.annotations = {}
if 'current_paper' not in st.session_state:
    st.session_state.current_paper = None

def format_pvalue(p_value):
    """Format p-value display: None/null → 'Non sig.', otherwise return as-is."""
    if p_value is None or p_value == 'None' or p_value == 'null' or p_value == '':
        return 'Non sig.'
    return str(p_value)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 4px solid #1f77b4;
}
.outcome-card {
    background-color: #ffffff;
    padding: 12px;
    border-radius: 5px;
    margin: 8px 0;
    border: 1px solid #e0e0e0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.phase-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    margin-right: 8px;
}
.phase-tei {
    background-color: #4CAF50;
    color: white;
}
.phase-pdf {
    background-color: #FF9800;
    color: white;
}
.stat-label {
    font-weight: 600;
    color: #555;
    font-size: 13px;
}
.stat-value {
    font-size: 16px;
    color: #1f77b4;
    font-weight: bold;
}
.table-summary {
    background-color: #fff3e0;
    padding: 10px;
    border-radius: 5px;
    margin: 8px 0;
    border-left: 3px solid #ff9800;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_available_papers():
    """Find all papers with Phase 6 results."""
    # Try all possible output locations (local run, deployed, and nested directory structure)
    possible_dirs = [
        Path("outputs/phase6"),
        Path("om_qex_extraction_v2/outputs/phase6"),
        Path("om_qex_extraction_v2/om_qex_extraction_v2/outputs/phase6")
    ]
    
    phase6_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            phase6_dir = dir_path
            break
    
    if not phase6_dir:
        return []
    
    papers = []
    # Phase 6 files are named *_final.json
    for json_file in phase6_dir.glob("*_final.json"):
        key = json_file.stem.replace("_final", "")
        papers.append(key)
    
    return sorted(papers)

@st.cache_data
def load_phase_result(key, phase):
    """Load result from a specific phase."""
    # Phase 6 uses different naming: *_final.json instead of *_phase6.json
    if phase == "6":
        possible_files = [
            Path(f"outputs/phase6/{key}_final.json"),
            Path(f"om_qex_extraction_v2/outputs/phase6/{key}_final.json"),
            Path(f"om_qex_extraction_v2/om_qex_extraction_v2/outputs/phase6/{key}_final.json")
        ]
    else:
        possible_files = [
            Path(f"outputs/phase{phase}/{key}_phase{phase}.json"),
            Path(f"om_qex_extraction_v2/outputs/phase{phase}/{key}_phase{phase}.json"),
            Path(f"om_qex_extraction_v2/om_qex_extraction_v2/outputs/phase{phase}/{key}_phase{phase}.json")
        ]
    
    phase_file = None
    for file_path in possible_files:
        if file_path.exists():
            phase_file = file_path
            break
    
    if not phase_file:
        return None
    
    try:
        with open(phase_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading phase {phase}: {e}")
        return None

def display_phase1_summary(phase1_data):
    """Display Phase 1: Table Discovery summary."""
    if not phase1_data:
        st.info("Phase 1 results not available")
        return
    
    st.markdown("### 📋 Phase 1: Table Discovery")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total = phase1_data.get('summary', {}).get('total_tables', 0)
        st.markdown(f'<div class="metric-card"><span class="stat-label">Total Tables Found</span><br><span class="stat-value">{total}</span></div>', unsafe_allow_html=True)
    
    with col2:
        structured = phase1_data.get('summary', {}).get('structured_tables', 0)
        st.markdown(f'<div class="metric-card"><span class="stat-label">Structured Tables</span><br><span class="stat-value">{structured}</span></div>', unsafe_allow_html=True)
    
    with col3:
        paragraph = phase1_data.get('summary', {}).get('paragraph_tables', 0)
        st.markdown(f'<div class="metric-card"><span class="stat-label">Paragraph Tables</span><br><span class="stat-value">{paragraph}</span></div>', unsafe_allow_html=True)
    
    # Show table list
    if st.checkbox("Show discovered tables", key="phase1_tables"):
        tables = phase1_data.get('tables', [])
        if tables:
            df = pd.DataFrame([
                {
                    'Table Number': t.get('table_number', 'unknown'),
                    'Type': t.get('table_type', 'unknown'),
                    'Caption': t.get('caption', 'No caption')[:80] + '...' if len(t.get('caption', '')) > 80 else t.get('caption', 'No caption')
                }
                for t in tables
            ])
            st.dataframe(df, use_container_width=True)

def display_phase2_summary(phase2_data):
    """Display Phase 2: Table Filtering summary."""
    if not phase2_data:
        st.info("Phase 2 results not available")
        return
    
    st.markdown("### 🎯 Phase 2: RESULTS Table Filtering")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        results = len(phase2_data.get('results_tables', []))
        st.markdown(f'<div class="metric-card" style="border-left-color: #4CAF50;"><span class="stat-label">RESULTS Tables</span><br><span class="stat-value" style="color: #4CAF50;">{results}</span></div>', unsafe_allow_html=True)
    
    with col2:
        excluded = len(phase2_data.get('excluded_tables', []))
        st.markdown(f'<div class="metric-card" style="border-left-color: #f44336;"><span class="stat-label">Excluded Tables</span><br><span class="stat-value" style="color: #f44336;">{excluded}</span></div>', unsafe_allow_html=True)
    
    with col3:
        confidence = phase2_data.get('results_tables', [{}])[0].get('confidence_score', 0) if phase2_data.get('results_tables') else 0
        st.markdown(f'<div class="metric-card"><span class="stat-label">Avg Confidence</span><br><span class="stat-value">{confidence:.1%}</span></div>', unsafe_allow_html=True)
    
    # Show RESULTS tables
    if st.checkbox("Show RESULTS tables", key="phase2_results"):
        results_tables = phase2_data.get('results_tables', [])
        if results_tables:
            df = pd.DataFrame([
                {
                    'Table': t.get('table_number', 'unknown'),
                    'Confidence': f"{t.get('confidence_score', 0):.1%}",
                    'Reason': t.get('classification_reason', 'N/A')[:100] + '...' if len(t.get('classification_reason', '')) > 100 else t.get('classification_reason', 'N/A')
                }
                for t in results_tables
            ])
            st.dataframe(df, use_container_width=True)

def display_phase3_summary(phase3_data):
    """Display Phase 3/3b: Extraction summary."""
    if not phase3_data:
        st.info("Phase 3 results not available")
        return
    
    st.markdown("### 📊 Phase 3: TEI + PDF Vision Extraction")
    
    # Check if supplemented with PDF
    supplemented = phase3_data.get('_supplemented_from_pdf', False)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_outcomes = len(phase3_data.get('outcomes', []))
        st.markdown(f'<div class="metric-card"><span class="stat-label">Total Outcomes</span><br><span class="stat-value">{total_outcomes}</span></div>', unsafe_allow_html=True)
    
    with col2:
        tei_outcomes = len([o for o in phase3_data.get('outcomes', []) if not o.get('_extraction_method')])
        st.markdown(f'<div class="metric-card" style="border-left-color: #4CAF50;"><span class="stat-label">TEI Extraction</span><br><span class="stat-value" style="color: #4CAF50;">{tei_outcomes}</span></div>', unsafe_allow_html=True)
    
    with col3:
        pdf_outcomes = len([o for o in phase3_data.get('outcomes', []) if o.get('_extraction_method') == 'pdf_vision'])
        st.markdown(f'<div class="metric-card" style="border-left-color: #FF9800;"><span class="stat-label">PDF Vision</span><br><span class="stat-value" style="color: #FF9800;">{pdf_outcomes}</span></div>', unsafe_allow_html=True)
    
    with col4:
        tables = len(set([o.get('table_number') or o.get('_table_number') for o in phase3_data.get('outcomes', [])]))
        st.markdown(f'<div class="metric-card"><span class="stat-label">Tables Extracted</span><br><span class="stat-value">{tables}</span></div>', unsafe_allow_html=True)
    
    if supplemented:
        st.info(f"📷 PDF Vision triggered for tables: {', '.join(phase3_data.get('_pdf_tables_extracted', []))}")

def display_phase6_summary(phase6_data):
    """Display Phase 6: Final Results summary."""
    if not phase6_data:
        st.info("Phase 6 results not available")
        return
    
    st.markdown("### ✅ Phase 6: Final Postprocessed Results")
    
    # Phase 6 uses 'records' not 'outcomes'
    records = phase6_data.get('records', [])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total = len(records)
        st.markdown(f'<div class="metric-card"><span class="stat-label">Final Outcomes</span><br><span class="stat-value">{total}</span></div>', unsafe_allow_html=True)
    
    with col2:
        complete = len([o for o in records if o.get('_completeness_score', 0) >= 0.7])
        st.markdown(f'<div class="metric-card" style="border-left-color: #4CAF50;"><span class="stat-label">High Quality (≥70%)</span><br><span class="stat-value" style="color: #4CAF50;">{complete}</span></div>', unsafe_allow_html=True)
    
    with col3:
        avg_completeness = sum([o.get('_completeness_score', 0) for o in records]) / max(len(records), 1)
        st.markdown(f'<div class="metric-card"><span class="stat-label">Avg Completeness</span><br><span class="stat-value">{avg_completeness:.1%}</span></div>', unsafe_allow_html=True)

def display_outcomes_table(outcomes):
    """Display outcomes in an interactive table."""
    if not outcomes:
        st.warning("No outcomes found")
        return
    
    # Prepare data for display
    df_data = []
    for idx, outcome in enumerate(outcomes, 1):
        # Determine extraction source
        extraction_method = outcome.get('_extraction_method', 'tei_extraction')
        source_badge = '🟢 TEI' if extraction_method != 'pdf_vision' else '🟠 PDF'
        
        # Get table number
        table_num = outcome.get('table_number', 'unknown')
        
        df_data.append({
            '#': idx,
            'Source': source_badge,
            'Table': str(table_num),
            'Outcome Name': str(outcome.get('outcome_name', 'N/A')),
            'Treatment Arm': str(outcome.get('treatment_arm', 'N/A')),
            'Coefficient': str(outcome.get('effect_size', 'N/A')),
            'SE': str(outcome.get('standard_error', 'N/A')),
            'P-value': format_pvalue(outcome.get('p_value')),
            'N': str(outcome.get('sample_size') or outcome.get('n_observations') or 'N/A')
        })
    
    df = pd.DataFrame(df_data)
    
    # Display with filters
    st.markdown("#### Extracted Outcomes")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        source_filter = st.multiselect(
            "Source",
            options=['🟢 TEI', '🟠 PDF'],
            default=['🟢 TEI', '🟠 PDF']
        )
    with col2:
        tables = sorted(df['Table'].unique())
        table_filter = st.multiselect(
            "Tables",
            options=tables,
            default=tables
        )
    
    # Apply filters
    filtered_df = df[
        df['Source'].isin(source_filter) &
        df['Table'].isin(table_filter)
    ]
    
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400
    )
    
    st.caption(f"Showing {len(filtered_df)} of {len(df)} outcomes")
    
    # Manual review section
    st.markdown("---")
    st.markdown("### 📝 Manual Review & Annotation")
    
    # Review controls at top
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("✅ Mark outcomes as Correct/Incorrect and add comments. Annotations are saved in session.")
    with col2:
        if st.button("💾 Download Reviews", use_container_width=True):
            download_annotations(outcomes)
    
    # Get filtered indices
    filtered_indices = filtered_df['#'].tolist()
    
    if filtered_indices:
        selected_outcome_num = st.selectbox(
            "Select outcome to review",
            filtered_indices,
            format_func=lambda x: f"#{x} - {outcomes[x-1].get('outcome_name', 'N/A')}"
        )
        
        outcome = outcomes[selected_outcome_num - 1]
        outcome_id = f"{st.session_state.current_paper}_{selected_outcome_num}"
        
        # Display outcome details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Outcome:** {outcome.get('outcome_name', 'N/A')}")
            st.markdown(f"**Table:** {outcome.get('table_number', 'N/A')}")
            st.markdown(f"**Coefficient:** {outcome.get('effect_size', 'N/A')} (SE: {outcome.get('standard_error', 'N/A')})")
            st.markdown(f"**P-value:** {format_pvalue(outcome.get('p_value'))}")
            
            if outcome.get('literal_text'):
                with st.expander("📄 Literal text from paper"):
                    st.code(outcome['literal_text'], language=None)
        
        with col2:
            st.markdown("**Review Status**")
            
            # Get current annotation
            current_annotation = st.session_state.annotations.get(outcome_id, {})
            
            # Review decision
            status = st.radio(
                "Status",
                options=["Not Reviewed", "✅ Correct", "❌ Incorrect"],
                index=["Not Reviewed", "✅ Correct", "❌ Incorrect"].index(current_annotation.get('status', 'Not Reviewed')),
                key=f"status_{outcome_id}"
            )
            
            # Comment
            comment = st.text_area(
                "Comments/Notes",
                value=current_annotation.get('comment', ''),
                placeholder="Add notes about this extraction...",
                key=f"comment_{outcome_id}",
                height=100
            )
            
            # Save button
            if st.button("💾 Save Review", key=f"save_{outcome_id}", use_container_width=True):
                st.session_state.annotations[outcome_id] = {
                    'outcome_number': selected_outcome_num,
                    'outcome_name': outcome.get('outcome_name', 'N/A'),
                    'table_number': outcome.get('table_number', 'N/A'),
                    'status': status,
                    'comment': comment,
                    'timestamp': datetime.now().isoformat(),
                    'reviewer': 'User'
                }
                st.success("✅ Review saved!")
        
        # Show review summary
        st.markdown("---")
        display_review_summary(outcomes)

def display_review_summary(outcomes):
    """Display summary of review progress."""
    st.markdown("### 📊 Review Progress")
    
    total = len(outcomes)
    reviewed = len([k for k, v in st.session_state.annotations.items() 
                   if k.startswith(f"{st.session_state.current_paper}_") and v.get('status') != 'Not Reviewed'])
    correct = len([k for k, v in st.session_state.annotations.items() 
                  if k.startswith(f"{st.session_state.current_paper}_") and v.get('status') == '✅ Correct'])
    incorrect = len([k for k, v in st.session_state.annotations.items() 
                    if k.startswith(f"{st.session_state.current_paper}_") and v.get('status') == '❌ Incorrect'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Outcomes", total)
    with col2:
        st.metric("Reviewed", f"{reviewed}/{total}", f"{reviewed/total*100:.0f}%" if total > 0 else "0%")
    with col3:
        st.metric("✅ Correct", correct)
    with col4:
        st.metric("❌ Incorrect", incorrect)
    
    # Show reviewed outcomes
    if reviewed > 0:
        with st.expander(f"View all {reviewed} reviewed outcomes"):
            review_data = []
            for idx, outcome in enumerate(outcomes, 1):
                outcome_id = f"{st.session_state.current_paper}_{idx}"
                if outcome_id in st.session_state.annotations:
                    ann = st.session_state.annotations[outcome_id]
                    if ann.get('status') != 'Not Reviewed':
                        review_data.append({
                            '#': idx,
                            'Outcome': outcome.get('outcome_name', 'N/A')[:50],
                            'Status': ann.get('status', 'N/A'),
                            'Comment': ann.get('comment', '')[:80] if ann.get('comment') else ''
                        })
            
            if review_data:
                review_df = pd.DataFrame(review_data)
                st.dataframe(review_df, use_container_width=True)

def download_annotations(outcomes):
    """Generate downloadable annotations file."""
    # Prepare annotations data
    annotations_data = []
    
    for idx, outcome in enumerate(outcomes, 1):
        outcome_id = f"{st.session_state.current_paper}_{idx}"
        annotation = st.session_state.annotations.get(outcome_id, {})
        
        annotations_data.append({
            'paper_key': st.session_state.current_paper,
            'outcome_number': idx,
            'outcome_name': outcome.get('outcome_name', 'N/A'),
            'table_number': outcome.get('table_number', 'N/A'),
            'extraction_method': outcome.get('_extraction_method', 'tei_extraction'),
            'effect_size': outcome.get('effect_size', 'N/A'),
            'standard_error': outcome.get('standard_error', 'N/A'),
            'p_value': outcome.get('p_value', 'N/A'),
            'review_status': annotation.get('status', 'Not Reviewed'),
            'reviewer_comment': annotation.get('comment', ''),
            'review_timestamp': annotation.get('timestamp', ''),
            'reviewer': annotation.get('reviewer', '')
        })
    
    # Convert to DataFrame
    annotations_df = pd.DataFrame(annotations_data)
    
    # Generate CSV
    csv = annotations_df.to_csv(index=False)
    
    # Create download button
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{st.session_state.current_paper}_review_{timestamp}.csv"
    
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )
    
    st.success(f"✅ Ready to download: {filename}")

def display_outcome_details(outcomes):
    """Display detailed view of individual outcomes."""
    if not outcomes:
        return
    
    st.markdown("#### Outcome Details")
    
    # Select outcome
    outcome_names = [f"{i+1}. {o.get('outcome_name', 'N/A')} (Table {o.get('table_number', '?')})" 
                    for i, o in enumerate(outcomes)]
    
    selected_idx = st.selectbox(
        "Select outcome to view details",
        range(len(outcome_names)),
        format_func=lambda i: outcome_names[i]
    )
    
    outcome = outcomes[selected_idx]
    
    # Display in expandable sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Basic Information")
        st.write(f"**Outcome Name:** {outcome.get('outcome_name', 'N/A')}")
        st.write(f"**Category:** {outcome.get('outcome_category', 'N/A')}")
        st.write(f"**Treatment Arm:** {outcome.get('treatment_arm', 'N/A')}")
        st.write(f"**Subgroup:** {outcome.get('subgroup', 'N/A')}")
        
        st.markdown("##### Extraction Source")
        extraction_method = outcome.get('_extraction_method', 'tei_extraction')
        if extraction_method == 'pdf_vision':
            st.write("🟠 **PDF Vision** (fallback extraction)")
            st.write(f"Page: {outcome.get('_page_number', 'N/A')}")
        else:
            st.write("🟢 **TEI Extraction** (primary)")
        st.write(f"Table: {outcome.get('table_number', 'N/A')}")
    
    with col2:
        st.markdown("##### Statistical Data")
        st.write(f"**Coefficient:** {outcome.get('effect_size', 'N/A')}")
        st.write(f"**Standard Error:** {outcome.get('standard_error', 'N/A')}")
        st.write(f"**P-value:** {format_pvalue(outcome.get('p_value'))}")
        st.write(f"**CI Lower:** {outcome.get('ci_lower', 'N/A')}")
        st.write(f"**CI Upper:** {outcome.get('ci_upper', 'N/A')}")
        st.write(f"**Sample Size:** {outcome.get('sample_size') or outcome.get('n_observations', 'N/A')}")
        
        if '_completeness_score' in outcome:
            completeness = outcome['_completeness_score']
            st.metric("Completeness Score", f"{completeness:.0%}")
    
    # Show literal text if available
    if outcome.get('literal_text'):
        with st.expander("📝 Literal Text from Paper"):
            st.code(outcome['literal_text'], language=None)
            if outcome.get('text_position'):
                st.caption(f"Location: {outcome['text_position']}")

def main():
    st.title("Outcomes Mapping LLM - validation")
    st.markdown("View extraction results from the V2 multi-phase pipeline.")
    
    # Add reviewer instruction banner
    st.info("👋 **For Reviewers:** Go to the **'Outcomes Table'** tab and scroll down to the **'Manual Review & Annotation'** section at the bottom to validate extracted outcomes.")
    
    # Sidebar: Paper selection
    with st.sidebar:
        st.header("📄 Paper Selection")
        
        papers = load_available_papers()
        
        if not papers:
            st.error("No extraction results found. Run the pipeline first.")
            st.info("Run: `python run_pipeline_v2.py --keys [KEYS] --phases 1,2,3,4,5,6`")
            return
        
        st.success(f"Found {len(papers)} papers with results")
        
        selected_paper = st.selectbox(
            "Select paper",
            papers,
            index=0
        )
        
        st.markdown("---")
        st.markdown("### Pipeline Phases")
        st.markdown("""
        - **Phase 1**: Table Discovery
        - **Phase 2**: RESULTS Filtering
        - **Phase 3**: TEI Extraction
        - **Phase 3b**: PDF Vision (fallback)
        - **Phase 4**: Outcome Mapping
        - **Phase 5**: QEX Extraction
        - **Phase 6**: Postprocessing
        """)
    
    # Main content
    if selected_paper:
        # Update current paper in session state
        st.session_state.current_paper = selected_paper
        
        st.header(f"Paper: {selected_paper}")
        
        # Load all phase results
        phase1_data = load_phase_result(selected_paper, "1")
        phase2_data = load_phase_result(selected_paper, "2")
        phase3_data = load_phase_result(selected_paper, "3")
        phase6_data = load_phase_result(selected_paper, "6")
        
        # Display tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Summary", 
            "🔍 Phase Details",
            "📋 Outcomes Table",
            "🔬 Outcome Details"
        ])
        
        with tab1:
            st.markdown("## Extraction Summary")
            display_phase1_summary(phase1_data)
            st.markdown("---")
            display_phase2_summary(phase2_data)
            st.markdown("---")
            display_phase3_summary(phase3_data)
            st.markdown("---")
            display_phase6_summary(phase6_data)
        
        with tab2:
            st.markdown("## Phase-by-Phase Details")
            
            phase_selection = st.selectbox(
                "Select phase to view",
                ["Phase 1: Table Discovery", 
                 "Phase 2: Table Filtering", 
                 "Phase 3: TEI Extraction",
                 "Phase 6: Final Results"]
            )
            
            if "Phase 1" in phase_selection and phase1_data:
                st.json(phase1_data)
            elif "Phase 2" in phase_selection and phase2_data:
                st.json(phase2_data)
            elif "Phase 3" in phase_selection and phase3_data:
                st.json(phase3_data)
            elif "Phase 6" in phase_selection and phase6_data:
                st.json(phase6_data)
        
        with tab3:
            # Phase 6 uses 'records' not 'outcomes'
            outcomes = phase6_data.get('records', []) if phase6_data else []
            display_outcomes_table(outcomes)
        
        with tab4:
            # Phase 6 uses 'records' not 'outcomes'
            outcomes = phase6_data.get('records', []) if phase6_data else []
            display_outcome_details(outcomes)

if __name__ == "__main__":
    main()
