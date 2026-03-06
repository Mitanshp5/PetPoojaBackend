import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

async def analyze_frequencies():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME")]

    orders = await db.orders.find({"items": {"$exists": True}}).to_list(length=20000)
    
    item_freq = defaultdict(int)
    pair_freq = defaultdict(int)

    for order in orders:
        tokens = list(set([i.get("menu_item_id") for i in order.get("items", []) if i.get("menu_item_id")]))
        for i in range(len(tokens)):
            item_freq[tokens[i]] += 1
            for j in range(i + 1, len(tokens)):
                pair = tuple(sorted([tokens[i], tokens[j]]))
                pair_freq[pair] += 1

    print(f"Total pairs found: {len(pair_freq)}")
    
    # Sort pairs by frequency
    sorted_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)
    
    print("\nTop 5 pairs by frequency:")
    for pair, freq in sorted_pairs[:5]:
        conf_a = (freq / item_freq[pair[0]]) * 100
        conf_b = (freq / item_freq[pair[1]]) * 100
        print(f"Pair {pair}: Freq={freq}, Conf A->B={conf_a:.1f}%, Conf B->A={conf_b:.1f}%")

    client.close()

if __name__ == "__main__":
    asyncio.run(analyze_frequencies())
