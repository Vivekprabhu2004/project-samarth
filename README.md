# Project Samarth - Intelligent Q&A System for Agricultural & Climate Data

An AI-powered system that answers natural language questions about Indian agricultural production and climate patterns by analyzing government datasets in real-time.

## 🎯 Overview

Project Samarth is an intelligent Q&A system that sources information directly from Indian government agricultural and meteorological datasets. It uses Google Gemini 2.0 Flash LLM with pandas for data processing to answer complex, cross-domain questions about India's agricultural economy and climate patterns.

## ✨ Key Features

- **Natural Language Q&A**: Ask questions in plain English about crop production, rainfall patterns, and correlations
- **Real-time Data Analysis**: Processes 246K+ crop production records and 2.3K+ rainfall records dynamically
- **Source Citations**: Every answer includes specific data source citations for traceability
- **Multi-dataset Synthesis**: Intelligently combines crop production and climate data for comprehensive insights
- **Clean UI**: Minimal, functional chat interface focused on accuracy and usability

## 📊 Datasets

### 1. Crop Production Data (1997-2015)
- **Source**: Ministry of Agriculture & Farmers Welfare
- **Records**: 246,091 rows
- **Coverage**: 33 states, 124 crops
- **Columns**: State, District, Year, Season, Crop, Area, Production

### 2. Rainfall Data (1951-2015)
- **Source**: India Meteorological Department (IMD)
- **Records**: 2,301 rows
- **Coverage**: Monthly, seasonal, and annual rainfall by subdivision/state

### 3. Social Groups Data
- **Source**: Agricultural Census
- **Records**: Holdings and operated area by size groups

## 🏗️ System Architecture

```
User Question → FastAPI Backend → QA Service (Gemini 2.0 Flash)
                                       ↓
                                 Determines data needs
                                       ↓
                                 Data Service (Pandas)
                                       ↓
                                 Queries CSV/Excel files
                                       ↓
                                 Returns aggregated data
                                       ↓
                                 LLM synthesizes answer
                                       ↓
                                 Response with citations
```

## 🔧 Technical Stack

**Backend:** FastAPI, Pandas, Google Gemini 2.0 Flash, MongoDB, Motor
**Frontend:** React 19, Shadcn UI, Tailwind CSS, Axios

## 📝 Sample Questions

1. "What are the top 5 most produced crops in Punjab between 2010-2015?"
2. "Analyze rice production trends in West Bengal from 2000 to 2015"
3. "Compare average annual rainfall in Maharashtra and Karnataka"
4. "Which district in Uttar Pradesh had highest wheat production in 2015?"

## 🚀 Quick Start

The application is already running. Access it at your deployment URL.

**Backend API**: `/api/*`
**Frontend**: Main URL

## 📡 API Endpoints

- `GET /api/data/summary` - Get dataset summary
- `POST /api/qa/ask` - Ask a question
- `GET /api/qa/history/{session_id}` - Get chat history
- `GET /api/qa/sessions` - List all sessions

## 🔒 Core Values

- **Accuracy**: Every data point cited with source
- **Traceability**: Full transparency on data origins
- **Privacy**: Secure deployment, data sovereignty
- **Extensibility**: Easy to add more data sources

## 📈 Future Enhancements

1. Live data integration with data.gov.in API
2. Advanced visualizations and trend charts
3. Multi-language support
4. Export capabilities (PDF/CSV reports)
5. More data sources (soil, irrigation, prices)

---

**Built for Project Samarth Challenge - Enabling data-driven policy making**
