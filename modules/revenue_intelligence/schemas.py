from pydantic import BaseModel
from typing import List, Dict, Optional

class MenuItemAnalysis(BaseModel):
    item_id: str
    name: str
    category: str
    selling_price: float
    food_cost: float
    contribution_margin: float
    margin_percentage: float
    sales_velocity: int # Quantity sold in period
    total_revenue: float
    classification: str # Star, Plowhorse, Puzzle, Dog
    price_optimization: str
    optimal_price: float

class MenuAnalysisResponse(BaseModel):
    items: List[MenuItemAnalysis]
    summary: Dict[str, int] # e.g. {"Star": 5, "Dog": 2}
    average_margin: float
    average_velocity: float

class ComboRecommendation(BaseModel):
    primary_item_id: str
    primary_item_name: str
    recommended_item_id: str
    recommended_item_name: str
    confidence_score: float # Percentage of times bought together

class ComboResponse(BaseModel):
    recommendations: List[ComboRecommendation]

class DailyTrend(BaseModel):
    day: str
    revenue: float
    orders: int

class TrendResponse(BaseModel):
    trends: List[DailyTrend]

