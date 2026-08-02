"""CSV data ingestion and fast memory lookup utility."""

import logging
import pandas as pd
from src.config import settings
from src.domain.models import GroupMemberMetadata, UserMetadata

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads relational context tables into efficient memory lookup mappings."""

    def __init__(self) -> None:
        self.users: dict[str, UserMetadata] = {}
        self.group_members: dict[tuple[str, str], GroupMemberMetadata] = {}
        self.business_accounts: dict[str, dict] = {}
        self.history_df = pd.DataFrame()

    def load_all(self) -> None:
        """Loads dataset CSV files from settings.dataset_dir into memory."""
        logger.info("Loading auxiliary metadata CSV files...")
        
        # Load Users dataset
        users_file = settings.dataset_dir / "users.csv"
        if users_file.exists():
            users_df = pd.read_csv(users_file)
            for _, r in users_df.iterrows():
                uid = str(r["user_id"])
                self.users[uid] = UserMetadata(
                    user_id=uid,
                    quiet_hours_start=r["quiet_hours_start"] if pd.notna(r.get("quiet_hours_start")) else None,
                    quiet_hours_end=r["quiet_hours_end"] if pd.notna(r.get("quiet_hours_end")) else None,
                )

        # Load Group Members dataset
        gm_file = settings.dataset_dir / "group_members.csv"
        if gm_file.exists():
            gm_df = pd.read_csv(gm_file)
            for _, r in gm_df.iterrows():
                key = (str(r["user_id"]), str(r["group_id"]))
                self.group_members[key] = GroupMemberMetadata(
                    user_id=str(r["user_id"]),
                    group_id=str(r["group_id"]),
                    is_muted=bool(r.get("is_muted", False)),
                    role=str(r.get("role", "member")),
                )

        # Load Business Accounts dataset
        biz_file = settings.dataset_dir / "business_accounts.csv"
        if biz_file.exists():
            biz_df = pd.read_csv(biz_file)
            for _, r in biz_df.iterrows():
                self.business_accounts[str(r["business_id"])] = r.to_dict()

        # Load Message History dataset
        history_file = settings.dataset_dir / "message_history.csv"
        if history_file.exists():
            self.history_df = pd.read_csv(history_file)

        logger.info("Context tables successfully loaded.")

    def get_user(self, user_id: str) -> UserMetadata:
        """Retrieves user metadata by user_id."""
        return self.users.get(str(user_id), UserMetadata(user_id=str(user_id)))

    def get_group_member(self, user_id: str, group_id: str) -> GroupMemberMetadata | None:
        """Retrieves user group metadata."""
        return self.group_members.get((str(user_id), str(group_id)))

    def get_context_summary(self, user_id: str, group_id: str | None = None, business_id: str | None = None) -> str:
        """Formats context variables into a clean string representation for prompts."""
        context = [f"Receiver User ID: {user_id}"]

        if group_id and group_id != "nan":
            gm = self.get_group_member(user_id, group_id)
            status = "Muted" if gm and gm.is_muted else "Active"
            context.append(f"Group ID: {group_id} (Group Setting: {status})")

        if business_id and business_id != "nan":
            biz = self.business_accounts.get(str(business_id), {})
            verified = biz.get("verified", "unknown")
            context.append(f"Business Sender ID: {business_id} (Verified: {verified})")
            
        return " | ".join(context)