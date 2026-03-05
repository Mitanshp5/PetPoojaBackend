from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from api.dependencies import get_db

from .schemas import MenuAnalysisResponse, ComboResponse
from .service import RevenueIntelligenceService

router = APIRouter(prefix="/revenue", tags=["Revenue Intelligence"])

def get_revenue_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> RevenueIntelligenceService:
    return RevenueIntelligenceService(db)

@router.get("/analysis", response_model=MenuAnalysisResponse)
async def get_menu_analysis(service: RevenueIntelligenceService = Depends(get_revenue_service)):
    """
    Returns the profitability and BCG matrix classification (Star, Plowhorse, Puzzle, Dog) for the menu.
    """
    return await service.analyze_menu_performance()

@router.get("/combos", response_model=ComboResponse)
async def get_combo_recommendations(service: RevenueIntelligenceService = Depends(get_revenue_service)):
    """
    Returns automated combo recommendations based on historical order association (Market Basket Analysis).
    """
    return await service.get_combo_recommendations()
