import os
import random
from datetime import datetime, timedelta

def generate_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "mock_discord_logs")
    os.makedirs(data_dir, exist_ok=True)

    noise_pool = [
        "Does anyone else think the overarching story is disconnected?",
        "Who cares about the lore when the ping is this bad? Fix your servers devs!",
        "The bright red minimap is literally burning my retinas. Please add a dark mode.",
        "The weapon balance in this patch is a joke. Assault rifle does zero damage.",
        "Guys how do I change my resolution? The slider is greyed out.",
        "honestly the lag is the real issue. get better internet.",
        "still waiting on that minimap color update...",
        "LF2M for the raid, need a healer and a tank.",
        "This game is literally unplayable right now.",
        "Can someone trade me 50 iron ingots? I'm stuck at the forge."
    ]

    bug_1_physics = [
        "Massive game-breaking issue in the Neon District level. Every time I trigger the high-speed dash near the server room walls, my kinematic body ignores the static collision mesh. https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2UxX2JzbDlyNQ==/template_primary",
        "I think the dash mechanic is broken? I dashed away from an enemy in the Neon District and clipped right through a solid wall. https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2UxX2JzbDlyNQ==/template_primary",
        "FIX THE DASH BUG IN NEON DISTRICT. I just fell through the floor AGAIN near the metro stairs.https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2UxX2JzbDlyNQ==/template_primary"
    ]

    bug_2_ui = [
        "Hey guys, is anyone else's game totally freezing when they open the inventory?https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2UyX2dzZnlpdw==/template_primary",
        "YES! It's specifically the plasma rifle. Every single time I try to equip it, the whole inventory screen hard crashes to the desktop.https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2UyX2dzZnlpdw==/template_primary",
        "Pls fix the plasma rifle bug. I just lost two hours of progress because I opened my inventory to swap weapons and the game completely froze.https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2UyX2dzZnlpdw==/template_primary"
    ]

    bug_3_audio = [
        "Anyone else getting massive audio delay on the Cyber-Dragon boss fight?",
        "The audio sync during the Chapter 4 boss is completely broken. The roar happens a full 5 seconds before the animation.",
        "Cyber-dragon fight is unplayable because the audio cues for his attacks are entirely desynced."
    ]

    bug_4_economy = [
        "URGENT: There is an infinite money glitch at the Blacksmith right now.",
        "If you sell an Iron Ingot to the Blacksmith and immediately buy it back by spamming the confirm button, it duplicates the item.",
        "People are abusing the Blacksmith sell exploit to get millions of gold. Economy is ruined.",
        "Please patch the ingot duplication glitch, everyone in my guild is doing it."
    ]

    bug_5_progression = [
        "DO NOT use the fast travel obelisk! My save file just corrupted.",
        "Game tried to auto-save while I was interacting with the fast travel point and my entire save is gone. 40 hours wasted.",
        "Fast travel auto-save bug is real. Game crashed during the load screen and now my file says 'Data Corrupted'.",
        "Warning: interacting with obelisks while the auto-save icon is spinning bricks your save file."
    ]

    bug_6_animation = [
        "Why is every NPC in the starting tavern stuck in a T-pose? https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2VzM194b3ZhZ3E=/template_primary",
        "The bartender isn't moving at all, just sliding around in a T-pose. Looks hilarious but needs fixing.",
        "T-pose glitch in the tavern. They still talk but their skeletons are completely frozen.https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2VzM194b3ZhZ3E=/template_primary",
        "All the guards in the main city are T-posing since the last hotfix.https://res-console.cloudinary.com/dfq6ylssz/thumbnails/transform/v1/image/upload/Y19maWxsLGhfMjAwLHdfMjAw/v1/aW1hZ2VzM194b3ZhZ3E=/template_primary"
    ]

    print(f"Generating 100 dense mock log files in {data_dir}...")
    
    start_time = datetime.now() - timedelta(days=2)
    bug_pools = [bug_1_physics, bug_2_ui, bug_3_audio, bug_4_economy, bug_5_progression, bug_6_animation]

    for i in range(1, 101):
        filename = f"discord_export_{i:03d}.txt"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            num_lines = random.randint(8, 20)
            for _ in range(num_lines):
                start_time += timedelta(minutes=random.randint(1, 10))
                timestamp = start_time.strftime("[%H:%M]")
                
                roll = random.random()
                if roll < 0.65:
                    msg = random.choice(noise_pool)
                else:
                    selected_bug_pool = random.choice(bug_pools)
                    msg = random.choice(selected_bug_pool)
                
                user = f"User{random.randint(1000, 9999)}"
                f.write(f"{timestamp} {user}: {msg}\n")

    print("Data generation complete. Six distinct systemic bugs successfully injected.")

if __name__ == "__main__":
    generate_data()