import asyncio
import data
import bot_modules.summon_sim as ss

asyncio.get_event_loop().run_until_complete(data.update_repositories())
showcase = ss.core.SimShowcaseCache.get("gala dragalia (apr 2020)")
rates = showcase.get_rates(0)
print("Expected outcome:")
print(rates.get_breakdown())

outcome = ss.pool.Rates()  # stores our outcomes
featured_pool = showcase.showcase.featured_adventurers + showcase.showcase.featured_dragons
for i in range(1000000):
    e = showcase.get_result(rates)
    outcome[e.rarity][e in featured_pool][type(e)] += 1.0
outcome.set_total(100)
print("\n\nSim results:")
print(outcome.get_breakdown())

