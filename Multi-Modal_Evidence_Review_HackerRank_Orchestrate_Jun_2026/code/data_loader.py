# Data handling layer to load our CSV references.
# This layer converts user history and baseline rules into optimized lookup maps, preventing heavy loop traversals on large files.

import pandas as pd
import os
from typing import Dict, List
from models import UserHistory, EvidenceRequirement

class ChallengeDataLoader:
    def __init__(self, dataset_dir: str = "../dataset"):
        self.dataset_dir = dataset_dir
        self.user_history: Dict[str, UserHistory] = {}
        self.requirements: List[EvidenceRequirement] = []

    def load_reference_data(self):
        # Load User History
        history_path = os.path.join(self.dataset_dir, "user_history.csv")

        if os.path.exists(history_path):
            df_hist = pd.read_csv(history_path)

            for _, row in df_hist.iterrows():
                uh = UserHistory(
                    user_id=str(row['user_id']),
                    past_claim_count=int(row['past_claim_count']),
                    accept_claim=int(row['accept_claim']),
                    manual_review_claim=int(row['manual_review_claim']),
                    rejected_claim=int(row['rejected_claim']),
                    last_90_days_claim_count=int(row['last_90_days_claim_count']),
                    history_flags=str(row['history_flags']),
                    history_summary=str(row['history_summary'])
                )
                self.user_history[uh.user_id] = uh

        # Load Evidence Requirements
        req_path = os.path.join(self.dataset_dir, "evidence_requirements.csv")

        if os.path.exists(req_path):
            df_req = pd.read_csv(req_path)
            
            for _, row in df_req.iterrows():
                req = EvidenceRequirement(
                    requirement_id=str(row['requirement_id']),
                    claim_object=row['claim_object'],
                    applies_to=str(row['applies_to']),
                    minimum_image_evidence=str(row['minimum_image_evidence'])
                )
                self.requirements.append(req)

    def get_user_context(self, user_id: str) -> Optional[UserHistory]:
        return self.user_history.get(user_id, None)

    def get_requirements_for_object(self, obj_type: str) -> List[EvidenceRequirement]:
        return [r for r in self.requirements if r.claim_object in (obj_type, "all")]