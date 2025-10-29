import google.generativeai as genai
import os
import json
import logging
from typing import Dict, Any, List
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from data_service import data_service

logger = logging.getLogger(__name__)

class QAService:
    def __init__(self):
        self.api_key = "AIzaSyCjAmF0iZsdvDiaCEn3DKpVA3C33KBNRMU"  # Provided Gemini API key
        if not self.api_key:
            raise ValueError("Gemini API key not found")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def analyze_question(self, question: str, session_id: str) -> Dict[str, Any]:
        """
        Analyze user question and generate answer using LLM with data context
        """
        try:
            # Get data summary for context
            data_summary = data_service.get_data_summary()
            
            # Create system message with data context
            system_message = f"""You are an intelligent Q&A assistant for Indian agricultural and climate data.

You have access to the following datasets:

1. **Crop Production Data** (1997-2015):
   - States: {len(data_summary.get('crop_production', {}).get('states', []))} states
   - Crops: {len(data_summary.get('crop_production', {}).get('crops', []))} different crops
   - Columns: State_Name, District_Name, Crop_Year, Season, Crop, Area, Production
   - Sample states: {', '.join(data_summary.get('crop_production', {}).get('states', [])[:10])}
   - Sample crops: {', '.join(data_summary.get('crop_production', {}).get('crops', [])[:15])}

2. **Rainfall Data** (1951-2015):
   - Subdivisions/States: {len(data_summary.get('rainfall', {}).get('subdivisions', []))} regions
   - Columns: SD_Name, YEAR, Monthly rainfall (JAN-DEC), ANNUAL, Seasonal totals
   - Sample subdivisions: {', '.join(data_summary.get('rainfall', {}).get('subdivisions', [])[:10])}

Your task:
1. Understand the user's question
2. Determine what data analysis is needed
3. I will execute the analysis and provide you with results
4. You synthesize a comprehensive answer with proper source citations

When you need data, respond in this JSON format:
{{
  "requires_data": true,
  "data_requests": [
    {{
      "type": "crop_production",
      "filters": {{"state": "State_Name", "year_start": 2000, "year_end": 2010, "crop": "Crop_Name"}}
    }},
    {{
      "type": "rainfall",
      "filters": {{"state": "State_Name", "year_start": 2000, "year_end": 2010}}
    }}
  ]
}}

After receiving data, provide a natural language answer that:
- Answers the question clearly
- Cites specific data sources
- Highlights key insights
- Mentions data limitations if any
"""
            
            # Initialize chat session
            chat = self.model.start_chat(history=[])

            # Send system message and question
            full_prompt = f"{system_message}\n\nUser Question: {question}"
            llm_response = await chat.send_message_async(full_prompt)
            llm_response = llm_response.text
            
            logger.info(f"LLM Response: {llm_response}")
            
            # Try to parse if LLM is requesting data
            # Clean response - remove markdown code blocks if present
            cleaned_response = llm_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            try:
                response_data = json.loads(cleaned_response)
                if response_data.get('requires_data'):
                    # Execute data requests
                    data_results = await self._execute_data_requests(response_data['data_requests'])
                    
                    # Send data back to LLM for final answer
                    data_prompt = f"Here is the data you requested:\n\n{json.dumps(data_results, indent=2)}\n\nPlease provide a comprehensive answer to the original question with proper citations. Do not use JSON format in your response - provide a natural language answer."
                    final_response = await chat.send_message_async(data_prompt)
                    final_response = final_response.text
                    
                    return {
                        'answer': final_response,
                        'data_sources': self._extract_sources(data_results),
                        'data_used': data_results
                    }
            except json.JSONDecodeError as e:
                # LLM provided direct answer
                logger.info(f"Could not parse as JSON (direct answer): {e}")
                pass
            
            return {
                'answer': llm_response,
                'data_sources': ['General knowledge'],
                'data_used': None
            }
            
        except Exception as e:
            logger.error(f"Error in QA service: {e}")
            raise
    
    async def _execute_data_requests(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute data requests and return results"""
        results = {}
        
        for i, request in enumerate(requests):
            req_type = request.get('type')
            filters = request.get('filters', {})
            
            try:
                if req_type == 'crop_production':
                    df = data_service.query_crop_data(filters)
                    if not df.empty:
                        # Aggregate data for summary
                        summary = {
                            'total_rows': len(df),
                            'states': df['State_Name'].unique().tolist(),
                            'crops': df['Crop'].unique().tolist(),
                            'year_range': [int(df['Crop_Year'].min()), int(df['Crop_Year'].max())],
                            'total_production': float(df['Production'].sum()),
                            'total_area': float(df['Area'].sum()),
                            'top_crops_by_production': df.groupby('Crop')['Production'].sum().sort_values(ascending=False).head(10).to_dict(),
                            'production_by_year': df.groupby('Crop_Year')['Production'].sum().to_dict(),
                            'districts': df['District_Name'].unique().tolist()[:20]
                        }
                        results[f'crop_data_{i}'] = summary
                    else:
                        results[f'crop_data_{i}'] = {'error': 'No data found for given filters'}
                
                elif req_type == 'rainfall':
                    df = data_service.query_rainfall_data(filters)
                    if not df.empty:
                        summary = {
                            'total_rows': len(df),
                            'subdivisions': df['SD_Name'].unique().tolist(),
                            'year_range': [int(df['YEAR'].min()), int(df['YEAR'].max())],
                            'average_annual_rainfall': float(df['ANNUAL'].mean()),
                            'min_rainfall': float(df['ANNUAL'].min()),
                            'max_rainfall': float(df['ANNUAL'].max()),
                            'rainfall_by_year': df.groupby('YEAR')['ANNUAL'].mean().to_dict()
                        }
                        results[f'rainfall_data_{i}'] = summary
                    else:
                        results[f'rainfall_data_{i}'] = {'error': 'No data found for given filters'}
                
            except Exception as e:
                logger.error(f"Error executing data request: {e}")
                results[f'error_{i}'] = str(e)
        
        return results
    
    def _extract_sources(self, data_results: Dict[str, Any]) -> List[str]:
        """Extract data source citations"""
        sources = set()
        
        for key in data_results.keys():
            if 'crop_data' in key:
                sources.add('Ministry of Agriculture & Farmers Welfare - Crop Production Dataset')
            elif 'rainfall_data' in key:
                sources.add('India Meteorological Department - Rainfall Dataset')
        
        return list(sources)

# Global instance
qa_service = QAService()