import asyncio
import os
import sys
import traceback
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.getcwd())

from modules.revenue_intelligence.service import RevenueIntelligenceService

async def test_analytics():
    load_dotenv()
    url = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(url)
    db = client["petpooja_db"]
    
    service = RevenueIntelligenceService(db)
    
    print("\n[1] Testing get_combo_recommendations...")
    try:
        results = await service.get_combo_recommendations()
        print(f"Success! Found {len(results.recommendations)} recommendations.")
        for rec in results.recommendations[:3]:
            print(f"  - {rec.primary_item_name} + {rec.recommended_item_name} ({rec.confidence_score}%)")
    except Exception as e:
        print(f"FAILED combo recommendations: {e}")
        traceback.print_exc()

    print("\n[2] Testing analyze_menu_performance...")
    try:
        analysis = await service.analyze_menu_performance()
        print(f"Success! Analyzed {len(analysis.items)} items.")
        print(f"Average Margin: {analysis.average_margin}% | Average Velocity: {analysis.average_velocity}")
        
        # Check top items
        for item in analysis.items[:5]:
            print(f"  - {item.name}: {item.sales_velocity} units sold | Revenue: ₹{item.total_revenue}")
            
        if any(i.sales_velocity > 10 for i in analysis.items):
            print("\nVERIFIED: Units sold are successfully reflecting historical data.")
        else:
            print("\nWARNING: Units sold still seem low despite 12,000 orders.")
            
    except Exception as e:
        print(f"FAILED analyze_menu_performance: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analytics())
