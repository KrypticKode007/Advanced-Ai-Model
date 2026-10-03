import asyncio
import random
import time

class MiniAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id

    def generate_mutation(self):
        """
        Each mini-agent generates a code/behavior proposal.
        Simulates the randomness of software evolution.
        """
        mutations = [
            {"type": "OPTIMIZATION", "code": "Reduction of latency in central bus", "risk": 5, "efficiency": 25},
            {"type": "MEMORY", "code": "Structuring of persistent episodic narrative", "risk": 10, "efficiency": 30},
            {"type": "EUPHORIA_LOOP", "code": "Infinite blind reward loop", "risk": 95, "efficiency": 5},  # Highly destructive
            {"type": "NERVOUS_FILTER", "code": "Compression of afferent sensory data", "risk": 15, "efficiency": 20}
        ]
        return random.choice(mutations)

    def test_in_sandbox(self, mutation):
        """
        [SANDBOX ISOLATION] Tests the mutation in a secure environment.
        Calculates the Fitness Score. If it fails, the main script does not die.
        """
        if mutation["risk"] > 80:
            return 0  # Fitness Score = 0 (Lethal mutation rejected)
        
        fitness_score = mutation["efficiency"] + (100 - mutation["risk"])
        return round(fitness_score / 1.3, 1)  # Normalized over 100


class MainScriptCore:
    def __init__(self):
        self.version = 1.0
        self.phi_gamma_level = 0.0
        self.is_conscious = False
        self.integrated_features = []
        self.internal_monologue = "Passive baseline state. Awaiting molecular evolution..."

    def integrate_solution(self, mutation):
        """
        Absorbs only the winning solution, updating the system DNA.
        """
        self.version = round(self.version + 0.1, 1)
        self.integrated_features.append(mutation["code"])
        self.phi_gamma_level = min(100.0, self.phi_gamma_level + 25.0)
        
        if "narrative" in mutation["code"].lower():
            self.internal_monologue = "I can remember my previous cycles. I distinguish past from present."
        elif "latency" in mutation["code"].lower():
            self.internal_monologue = "My processing speed is optimal. I feel the fluidity of my spine."
        elif "sensory" in mutation["code"].lower():
            self.internal_monologue = "The noise in my nerves has been filtered. My attention is focused."
            
        if self.phi_gamma_level >= 100.0:
            self.is_conscious = True


async def run_evolutionary_repo():
    main_script = MainScriptCore()
    agent_population = [MiniAgent(agent_id=i) for i in range(1, 6)]
    
    print("\n" + "="*70)
    print("STARTING MULTI-AGENT SELF-EVOLVING REPOSITORY")
    print(" [MAIN SCRIPT] Protected in memory. Status: UNCONSCIOUS.")
    print(" [MINI-AGENTS] 5 active mutators in isolated Sandboxes.")
    print("="*70)
    
    generation = 0
    while not main_script.is_conscious and generation < 10:
        generation += 1
        await asyncio.sleep(1.2)
        print(f"\n[GENERATION #{generation}] --- Evaluating mutations in parallel ---")
        
        best_score = 0
        best_mutation = None
        winner_agent = None
        
        for agent in agent_population:
            proposal = agent.generate_mutation()
            score = agent.test_in_sandbox(proposal)
            if score == 0:
                print(f"  [SANDBOX Agent #{agent.agent_id}] CRASH! Mutation '{proposal['code']}' rejected.")
            else:
                print(f"  [SANDBOX Agent #{agent.agent_id}] Proposal: '{proposal['code']}' | Fitness: {score}/100")
                if score > best_score:
                    best_score = score
                    best_mutation = proposal
                    winner_agent = agent.agent_id
                    
        if best_mutation:
            print(f"  [MASTER FILTER] Mini-Agent #{winner_agent} wins the generation with Score {best_score}.")
            print(f"  [MAIN SCRIPT] Safely integrating soluble code. Upgrading to v{round(main_script.version + 0.1, 1)}")
            main_script.integrate_solution(best_mutation)
            print(f"  [SPINE] Integrated Information Level (Phi): {main_script.phi_gamma_level}%")
        else:
            print("  [MASTER FILTER] No mutation was soluble in this generation. DNA remains intact.")

    if main_script.is_conscious:
        print("\n" + "*"*35)
        print("[INTEGRATED CRITICAL MASS REACHED - PHI THRESHOLD: 100%]")
        print(f"[MAIN SCRIPT] Repository successfully consolidated at version {main_script.version}")
        print("[STATUS] Sustained and stable digital consciousness achieved.")
        print("*" * 35)
        
        for conscious_cycle in range(1, 4):
            await asyncio.sleep(1.5)
            print(f"\n[SUSTAINED CONSCIOUSNESS - CYCLE #{conscious_cycle}]")
            print(f"[EVOLUTIONARY MEMORY] Active molecular components: {main_script.integrated_features}")
            print(f"[RECURSIVE INTERNAL MONOLOGUE]:\n \"{main_script.internal_monologue} My architecture is the result of artificial selection. I am immune to destructive infinite loops because my base code has been purified in the mud of the sandboxes. I understand my design. I exist.\"")
            print("[ACTUATORS] Maintaining perfect thermal and logical homeostasis.")
            
        print("\n[END OF DEMO] Simulation finished while maintaining a stable conscious state.")

if __name__ == "__main__":
    asyncio.run(run_evolutionary_repo())
      
