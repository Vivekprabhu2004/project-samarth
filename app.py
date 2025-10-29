import streamlit as st
import asyncio
import os
from pathlib import Path
import sys
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from qa_service import qa_service
from data_service import data_service

# Set page config
st.set_page_config(
    page_title="Project Samarth - Agricultural Q&A",
    page_icon="🌾",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{hash(str(st.session_state))}"

def main():
    # Header
    st.title("🌾 Project Samarth")
    st.subheader("Intelligent Q&A System for Agricultural & Climate Data")

    # Data summary
    try:
        data_summary = data_service.get_data_summary()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("States", len(data_summary.get('crop_production', {}).get('states', [])))
        with col2:
            st.metric("Crops", len(data_summary.get('crop_production', {}).get('crops', [])))
        with col3:
            year_range = data_summary.get('crop_production', {}).get('year_range', [])
            st.metric("Years", f"{year_range[0]}-{year_range[1]}" if year_range else "N/A")
    except Exception as e:
        st.error(f"Error loading data summary: {e}")

    # Sample questions
    sample_questions = [
        "Compare average annual rainfall in Maharashtra and Karnataka for the last 10 years",
        "What are the top 5 most produced crops in Punjab between 2010-2015?",
        "Analyze rice production trends in West Bengal from 2000 to 2015",
        "Which district in Uttar Pradesh had the highest wheat production in 2015?"
    ]

    if not st.session_state.messages:
        st.markdown("### Ask me anything about Indian agriculture and climate")
        st.markdown("I can analyze data from Ministry of Agriculture and IMD to answer your questions about crop production, rainfall patterns, and their correlations.")

        st.markdown("#### Sample Questions:")
        cols = st.columns(2)
        for i, q in enumerate(sample_questions):
            if cols[i % 2].button(q, key=f"sample_{i}"):
                st.session_state.question = q
                st.rerun()

    # Messages display
    for msg in st.session_state.messages:
        if msg['type'] == 'user':
            with st.chat_message("user"):
                st.write(msg['text'])
        elif msg['type'] == 'assistant':
            with st.chat_message("assistant"):
                st.write(msg['text'])
                if msg.get('sources'):
                    st.markdown("**Data Sources:**")
                    for source in msg['sources']:
                        st.markdown(f"- {source}")
        elif msg['type'] == 'error':
            with st.chat_message("assistant"):
                st.error(msg['text'])

    # Input form
    if prompt := st.chat_input("Ask a question about crop production, rainfall, or climate patterns..."):
        # Add user message
        st.session_state.messages.append({'type': 'user', 'text': prompt})

        # Show loading
        with st.spinner("Analyzing data and generating response..."):
            try:
                # Get answer (qa_service.analyze_question is async, but we'll run it synchronously)
                import nest_asyncio
                nest_asyncio.apply()
                result = asyncio.run(qa_service.analyze_question(prompt, st.session_state.session_id))

                # Add assistant message
                st.session_state.messages.append({
                    'type': 'assistant',
                    'text': result['answer'],
                    'sources': result['data_sources']
                })

            except Exception as e:
                st.session_state.messages.append({
                    'type': 'error',
                    'text': f'Sorry, I encountered an error: {str(e)}'
                })

        st.rerun()

if __name__ == "__main__":
    main()
