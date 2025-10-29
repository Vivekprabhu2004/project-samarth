import pandas as pd
import os
from pathlib import Path
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.data_dir = Path(__file__).parent / 'data'
        self.crop_df = None
        self.rainfall_df = None
        self.social_df = None
        self.load_data()
    
    def load_data(self):
        """Load all datasets into memory"""
        try:
            # Load crop production data
            crop_path = self.data_dir / 'crop_production.csv'
            if crop_path.exists():
                self.crop_df = pd.read_csv(crop_path)
                logger.info(f"Loaded crop data: {self.crop_df.shape[0]} rows")
            
            # Load rainfall data
            rainfall_path = self.data_dir / 'rainfall.xls'
            if rainfall_path.exists():
                self.rainfall_df = pd.read_excel(rainfall_path)
                logger.info(f"Loaded rainfall data: {self.rainfall_df.shape[0]} rows")
            
            # Load social groups data
            social_path = self.data_dir / 'social_groups.csv'
            if social_path.exists():
                self.social_df = pd.read_csv(social_path)
                logger.info(f"Loaded social groups data: {self.social_df.shape[0]} rows")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of available datasets"""
        summary = {}
        
        if self.crop_df is not None:
            summary['crop_production'] = {
                'rows': len(self.crop_df),
                'columns': list(self.crop_df.columns),
                'states': sorted(self.crop_df['State_Name'].unique().tolist()),
                'crops': sorted(self.crop_df['Crop'].unique().tolist()),
                'year_range': [int(self.crop_df['Crop_Year'].min()), int(self.crop_df['Crop_Year'].max())],
                'seasons': sorted(self.crop_df['Season'].unique().tolist())
            }
        
        if self.rainfall_df is not None:
            summary['rainfall'] = {
                'rows': len(self.rainfall_df),
                'columns': list(self.rainfall_df.columns),
                'subdivisions': sorted(self.rainfall_df['SD_Name'].unique().tolist()),
                'year_range': [int(self.rainfall_df['YEAR'].min()), int(self.rainfall_df['YEAR'].max())]
            }
        
        if self.social_df is not None:
            summary['social_groups'] = {
                'rows': len(self.social_df),
                'columns': list(self.social_df.columns)
            }
        
        return summary
    
    def query_crop_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Query crop production data with filters"""
        if self.crop_df is None:
            return pd.DataFrame()
        
        df = self.crop_df.copy()
        
        if 'state' in filters:
            df = df[df['State_Name'].str.contains(filters['state'], case=False, na=False)]
        
        if 'crop' in filters:
            df = df[df['Crop'].str.contains(filters['crop'], case=False, na=False)]
        
        if 'year_start' in filters:
            df = df[df['Crop_Year'] >= filters['year_start']]
        
        if 'year_end' in filters:
            df = df[df['Crop_Year'] <= filters['year_end']]
        
        if 'season' in filters:
            df = df[df['Season'].str.contains(filters['season'], case=False, na=False)]
        
        return df
    
    def query_rainfall_data(self, filters: Dict[str, Any]) -> pd.DataFrame:
        """Query rainfall data with filters"""
        if self.rainfall_df is None:
            return pd.DataFrame()
        
        df = self.rainfall_df.copy()
        
        if 'subdivision' in filters or 'state' in filters:
            search_term = filters.get('subdivision') or filters.get('state')
            df = df[df['SD_Name'].str.contains(search_term, case=False, na=False)]
        
        if 'year_start' in filters:
            df = df[df['YEAR'] >= filters['year_start']]
        
        if 'year_end' in filters:
            df = df[df['YEAR'] <= filters['year_end']]
        
        return df
    
    def get_crop_production_by_state(self, state: str, year_start: int, year_end: int, crop: str = None) -> Dict[str, Any]:
        """Get crop production statistics by state"""
        filters = {'state': state, 'year_start': year_start, 'year_end': year_end}
        if crop:
            filters['crop'] = crop
        
        df = self.query_crop_data(filters)
        
        if df.empty:
            return {'error': 'No data found'}
        
        # Group by crop and calculate total production
        crop_stats = df.groupby('Crop').agg({
            'Production': 'sum',
            'Area': 'sum'
        }).sort_values('Production', ascending=False)
        
        return {
            'state': state,
            'year_range': [year_start, year_end],
            'total_production': float(df['Production'].sum()),
            'total_area': float(df['Area'].sum()),
            'top_crops': crop_stats.head(10).to_dict('index'),
            'districts': df['District_Name'].unique().tolist()
        }
    
    def get_rainfall_by_state(self, state: str, year_start: int, year_end: int) -> Dict[str, Any]:
        """Get rainfall statistics by state"""
        filters = {'state': state, 'year_start': year_start, 'year_end': year_end}
        df = self.query_rainfall_data(filters)
        
        if df.empty:
            return {'error': 'No data found'}
        
        return {
            'state': state,
            'year_range': [year_start, year_end],
            'average_annual_rainfall': float(df['ANNUAL'].mean()),
            'min_rainfall': float(df['ANNUAL'].min()),
            'max_rainfall': float(df['ANNUAL'].max()),
            'yearly_data': df[['YEAR', 'ANNUAL']].to_dict('records')
        }

# Global instance
data_service = DataService()