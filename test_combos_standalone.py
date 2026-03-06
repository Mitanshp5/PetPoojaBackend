import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.getcwd())

from modules.revenue_intelligence.service import RevenueIntelligenceService

async def test_combos():
    load_dotenv()
    url = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(url)
    db = client["petpooja_db"]
    
    service = RevenueIntelligenceService(db)
    print("Running get_combo_recommendations...")
    try:
        results = await service.get_combo_recommendations()
        print(f"Success! Found {len(results.recommendations)} recommendations.")
    print("Running analyze_menu_performance...")
    try:
        analysis = await service.analyze_menu_performance()
        print(f"Success! Analyzed {len(analysis.items)} items.")
        print(f"Average Margin: {analysis.average_margin}% | Average Velocity: {analysis.average_velocity}")
        
        # Check top items
        for item in analysis.items[:5]:
            print(f"  {item.name}: {item.sales_velocity} units sold | Revenue: ₹{item.total_revenue}")
            
        if any(i.sales_velocity > 10 for i in analysis.items):
            print("VERIFIED: Units sold are successfully reflecting historical data.")
        else:
            print("WARNING: Units sold still seem low despite 12,000 orders.")
            
    except Exception as e:
        print(f"FAILED analyze_menu_performance: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_combos())
