class break_management:
    """Manages network breaks for systems and protocols"""
    
    def __init__(self):
        self.broken_services = set()
    
    def get_service_names(self):
        """Return list of all available services"""
        return []
    
    def trigger_break(self, team_idx, service_idx):
        """Trigger a break for a specific service"""
        key = f"{team_idx}:{service_idx}"
        self.broken_services.add(key)
        print(f"Triggered break for team {team_idx}, service {service_idx}")
    
    def trigger_unbreak(self, team_idx, service_idx):
        """Remove a break for a specific service"""
        key = f"{team_idx}:{service_idx}"
        self.broken_services.discard(key)
        print(f"Triggered unbreak for team {team_idx}, service {service_idx}")
