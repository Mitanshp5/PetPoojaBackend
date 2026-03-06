from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from collections import defaultdict
from typing import List, Dict
import math

from .schemas import MenuItemAnalysis, MenuAnalysisResponse, ComboRecommendation, ComboResponse

class RevenueIntelligenceService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.items_col = self.db["menu_items"]
        self.orders_col = self.db["orders"]

    async def analyze_menu_performance(self) -> MenuAnalysisResponse:
        """
        Calculates contribution margins, sales velocity, and BCG Matrix classification.
        """
        items_cursor = self.items_col.find({"is_active": True})
        items = await items_cursor.to_list(length=1000)
        
        if not items:
            return MenuAnalysisResponse(items=[], summary={}, average_margin=0, average_velocity=0)

        item_map = {str(item["_id"]): item for item in items}
        
        # 1. Calculate Sales Velocity (Quantity Sold) from Orders
        # Aggregation to get total quantity sold per item
        pipeline = [
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.menu_item_id",
                "total_quantity": {"$sum": "$items.quantity"},
                "total_revenue": {"$sum": {"$multiply": ["$items.quantity", 0]}} # Placeholder if we don't have price at order time, we calculate it 
            }}
        ]
        
        velocity_results = await self.orders_col.aggregate(pipeline).to_list(length=1000)
        velocity_map = {res["_id"]: res["total_quantity"] for res in velocity_results}

        analysis_results: List[MenuItemAnalysis] = []
        total_margin_pct = 0
        total_velocity = 0

        # 2. Calculate Margins and Prepare Data
        for item_id_str, item in item_map.items():
            selling_price = item.get("selling_price", 0)
            food_cost = item.get("food_cost", 0)
            
            margin = selling_price - food_cost
            margin_pct = (margin / selling_price * 100) if selling_price > 0 else 0
            
            velocity = velocity_map.get(item_id_str, 0)
            revenue = velocity * selling_price

            total_margin_pct += margin_pct
            total_velocity += velocity

            analysis_results.append(MenuItemAnalysis(
                item_id=item_id_str,
                name=item["name"],
                category=item.get("category", "Uncategorized"),
                selling_price=selling_price,
                food_cost=food_cost,
                contribution_margin=round(margin, 2),
                margin_percentage=round(margin_pct, 2),
                sales_velocity=velocity,
                total_revenue=round(revenue, 2),
                classification="Unclassified", # Computed next
                price_optimization="", # Computed next
                optimal_price=0.0 # Computed next
            ))

        # 3. Dynamic BCG Matrix Classification
        # We use the average margin and average velocity of the menu to draw the quadrants
        avg_margin = total_margin_pct / len(analysis_results)
        avg_velocity = total_velocity / len(analysis_results)

        summary_counts = {"Star": 0, "Plowhorse": 0, "Puzzle": 0, "Dog": 0}

        for result in analysis_results:
            is_high_margin = result.margin_percentage >= avg_margin
            is_high_volume = result.sales_velocity >= avg_velocity

            if is_high_margin and is_high_volume:
                result.classification = "Star"
                result.price_optimization = "Highly profitable & popular. Recommended action: Test a 3-5% price increase to maximize AOV without hurting volume."
                result.optimal_price = round(result.selling_price * 1.05, 2)
            elif not is_high_margin and is_high_volume:
                result.classification = "Plowhorse"  # Risk: low margin, takes up kitchen time
                result.price_optimization = "High volume but low margin. Recommended action: Raise price slightly or review raw ingredient costs to improve margins."
                result.optimal_price = round(result.selling_price * 1.08, 2)
            elif is_high_margin and not is_high_volume:
                result.classification = "Puzzle"     # Opportunity: needs promotion
                result.price_optimization = "High margin but low sales. Recommended action: Feature prominently on the menu, run specials, or bundle into combos."
                result.optimal_price = result.selling_price # Keep same, but promote
            else:
                result.classification = "Dog"        # Consider removing
                result.price_optimization = "Low margin & low sales volume. Recommended action: Standardize recipe to cut costs, or remove from menu entirely to reduce inventory waste."
                result.optimal_price = result.selling_price # Or liquidate

            summary_counts[result.classification] += 1

        # Sort by revenue descending
        analysis_results.sort(key=lambda x: x.total_revenue, reverse=True)

        return MenuAnalysisResponse(
            items=analysis_results,
            summary=summary_counts,
            average_margin=round(avg_margin, 2),
            average_velocity=round(avg_velocity, 2)
        )

    async def get_combo_recommendations(self, minimum_support: int = 5) -> ComboResponse:
        """
        Simple Association Rule logic (Market Basket Analysis) to find items frequently bought together.
        """
        # Fetch all orders to analyze items
        orders_cursor = self.orders_col.find({"items": {"$exists": True, "$not": {"$size": 0}}})
        orders = await orders_cursor.to_list(length=5000)

        items_cursor = self.items_col.find()
        items = await items_cursor.to_list(length=1000)
        item_names = {str(item["_id"]): item["name"] for item in items}

        # Track how many times each item is bought, and how many times pairs are bought
        item_frequencies = defaultdict(int)
        pair_frequencies = defaultdict(int)

        for order in orders:
            order_items = [i["menu_item_id"] for i in order.get("items", [])]
            # Deduplicate items in a single order (we care about distinct items bought together)
            unique_items = list(set(order_items))

            for i in range(len(unique_items)):
                item_1 = unique_items[i]
                item_frequencies[item_1] += 1

                for j in range(i + 1, len(unique_items)):
                    item_2 = unique_items[j]
                    # Create a sorted tuple to treat (A,B) the same as (B,A) for pair counting
                    pair = tuple(sorted([item_1, item_2]))
                    pair_frequencies[pair] += 1

        recommendations = []

        # Calculate confidence
        for pair, freq in pair_frequencies.items():
            if freq >= minimum_support:
                item_a, item_b = pair
                
                # Confidence A -> B = P(A & B) / P(A)
                conf_a_b = (freq / item_frequencies[item_a]) * 100
                # Confidence B -> A = P(A & B) / P(B)
                conf_b_a = (freq / item_frequencies[item_b]) * 100

                # We can generate two directional recommendations or just pick the strongest
                if conf_a_b > 30.0: # Only suggest if there's a >30% chance
                    recommendations.append(ComboRecommendation(
                        primary_item_id=item_a,
                        primary_item_name=item_names.get(item_a, "Unknown"),
                        recommended_item_id=item_b,
                        recommended_item_name=item_names.get(item_b, "Unknown"),
                        confidence_score=round(conf_a_b, 1)
                    ))
                
                if conf_b_a > 30.0:
                    recommendations.append(ComboRecommendation(
                        primary_item_id=item_b,
                        primary_item_name=item_names.get(item_b, "Unknown"),
                        recommended_item_id=item_a,
                        recommended_item_name=item_names.get(item_a, "Unknown"),
                        confidence_score=round(conf_b_a, 1)
                    ))

        # Sort by confidence score descending
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)

        return ComboResponse(recommendations=recommendations[:20]) # Return top 20
