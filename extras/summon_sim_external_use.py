# tests the optimal number of singles to perform before you start to use tenfolds
# will take some time to run due to the high number of iterations

import asyncio
import data
import bot_modules.summon_sim as ss
import time

asyncio.get_event_loop().run_until_complete(data.update_repositories())
showcase: ss.core.SimShowcase = ss.core.SimShowcaseCache.get("nadine and linnea's united front")

featured_pool = showcase.showcase.featured_adventurers + showcase.showcase.featured_dragons

print("data downloaded")
print("summoning on nadine and linnea's united front")
start_time = time.perf_counter()

target_five_stars = 1000000
for target_initial_solos in list(range(0, 50, 10)):
    total_five_stars = 0
    total_summons = 0
    pity_progress = 0
    while total_five_stars < target_five_stars:
        if pity_progress < target_initial_solos:
            e, pity_progress = showcase.perform_solo(pity_progress)
            total_summons += 1
            total_five_stars += 1 if e.rarity == 5 else 0
        else:
            entities, pity_progress = showcase.perform_tenfold(pity_progress)
            total_summons += 10
            total_five_stars += sum(1 for e in entities if e.rarity == 5)

    print(f"{target_initial_solos} solos:")
    print(f"  {total_five_stars:,} 5*")
    print(f"  {total_summons:,} summons")
    print(f"  {100*total_five_stars/total_summons:0.4f}% 5* rate")
