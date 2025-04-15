"""
Insurgent Missions for D&D Players
Each mission includes objectives, potential challenges, and rewards.
"""

def get_insurgent_missions():
    missions = [
        {
            "name": "The Supply Line Sabotage",
            "description": "A powerful noble is using their influence to hoard essential supplies, causing suffering among the common folk.",
            "objectives": [
                "Infiltrate the noble's warehouse district",
                "Locate and sabotage the supply chain",
                "Steal and redistribute supplies to the needy",
                "Escape without leaving evidence"
            ],
            "challenges": [
                "Heavily guarded warehouses",
                "Complex security systems",
                "Potential informants",
                "Time pressure to complete the mission"
            ],
            "rewards": [
                "Gain favor with the common folk",
                "Valuable stolen supplies",
                "Information about other corrupt nobles",
                "Experience points and gold"
            ]
        },
        {
            "name": "The Underground Network",
            "description": "Establish a network of informants and safe houses throughout the city to support the resistance movement.",
            "objectives": [
                "Recruit trustworthy informants from different social classes",
                "Set up secure meeting locations",
                "Create a communication system",
                "Protect the network from infiltration"
            ],
            "challenges": [
                "Identifying loyal informants",
                "Avoiding city guards and spies",
                "Maintaining secrecy",
                "Managing conflicting loyalties"
            ],
            "rewards": [
                "Valuable intelligence network",
                "Safe houses for future missions",
                "Allies in various social circles",
                "Experience points and influence"
            ]
        },
        {
            "name": "The False Flag Operation",
            "description": "Frame a rival faction for a crime to weaken their influence and strengthen the resistance's position.",
            "objectives": [
                "Gather evidence against the target faction",
                "Create convincing false evidence",
                "Execute the operation without being caught",
                "Ensure the blame falls on the intended target"
            ],
            "challenges": [
                "Creating believable evidence",
                "Avoiding detection during setup",
                "Timing the operation perfectly",
                "Dealing with unexpected witnesses"
            ],
            "rewards": [
                "Weakened rival faction",
                "Increased influence for the resistance",
                "Valuable intelligence",
                "Experience points and reputation"
            ]
        },
        {
            "name": "The Prison Break",
            "description": "Rescue captured resistance members from a high-security prison before they can be interrogated.",
            "objectives": [
                "Gather intelligence about the prison layout",
                "Infiltrate the prison complex",
                "Locate and free the prisoners",
                "Escape with all prisoners alive"
            ],
            "challenges": [
                "Heavy security presence",
                "Complex prison layout",
                "Limited time before reinforcements arrive",
                "Managing multiple NPCs during escape"
            ],
            "rewards": [
                "Freed resistance members",
                "Gained valuable allies",
                "Prison layout intelligence",
                "Experience points and renown"
            ]
        }
    ]
    return missions

if __name__ == "__main__":
    missions = get_insurgent_missions()
    for mission in missions:
        print(f"\nMission: {mission['name']}")
        print(f"Description: {mission['description']}")
        print("\nObjectives:")
        for obj in mission['objectives']:
            print(f"- {obj}")
        print("\nChallenges:")
        for challenge in mission['challenges']:
            print(f"- {challenge}")
        print("\nRewards:")
        for reward in mission['rewards']:
            print(f"- {reward}")
        print("\n" + "="*50) 