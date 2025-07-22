from typing import Dict, List, Set
from datetime import datetime

class Tusovka:
    def __init__(self):
        self.participants: Dict[int, str] = {}
        self.expenses: List[Expense] = []

class Expense:
    def __init__(self):
        self.payer_id: int = 0
        self.amount: float = 0.0
        self.description: str = ""
        self.targets: Set[int] = set()
        self.datetime: str = datetime.now().isoformat()