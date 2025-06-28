import asyncio
from typing import Any, Dict, List

import httpx

from supabase import Client, create_client


class JobScraper:
    def __init__(self, supabase_url: str, supabase_key: str, browser_use_api_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.browser_use_api_key = browser_use_api_key
        self.browser_use_base_url = "https://api.browser-use.com/api/v1"

    async def scrape_candidates(
        self,
        portal_url: str,
        username: str,
        password: str,
        position_name: str,
        company_name: str,
    ) -> Dict[str, int]:
        """
        Main scraping workflow:
        1. Create/get company and position
        2. Get existing phone hashes for this position
        3. Run Browser-Use task
        4. Process and store candidates
        """

        # Step 1: Ensure company and position exist
        company_id = await self._ensure_company(company_name)
        position_id = await self._ensure_position(company_id, position_name)

        # Step 2: Get existing phone hashes to avoid duplicates
        existing_hashes = await self._get_existing_phone_hashes(position_id)
        skip_hashes_csv = ",".join(existing_hashes)

        # Step 3: Prepare Browser-Use task
        task_payload = {
            "task": self._build_scraping_task(portal_url, position_name),
            "secrets": {
                "username": username,
                "password": password,
                "skip_hashes_csv": skip_hashes_csv,
            },
            "allowed_domains": [self._extract_domain(portal_url)],
            "structured_output_json": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                    },
                },
            },
            "save_browser_data": True,
        }

        # Step 4: Execute Browser-Use task
        candidates_data = await self._run_browser_use_task(task_payload)

        # Step 5: Store candidates in database
        result = await self._store_candidates(position_id, candidates_data, portal_url)

        return result

    async def _ensure_company(self, company_name: str) -> str:
        """Create or get company record"""
        # Try to get existing company
        result = (
            self.supabase.table("companies")
            .select("id")
            .eq("name", company_name)
            .execute()
        )

        if result.data:
            return result.data[0]["id"]

        # Create new company
        result = (
            self.supabase.table("companies").insert({"name": company_name}).execute()
        )
        return result.data[0]["id"]

    async def _ensure_position(self, company_id: str, position_title: str) -> str:
        """Create or get position record"""
        # Try to get existing position
        result = (
            self.supabase.table("positions")
            .select("id")
            .eq("company_id", company_id)
            .eq("title", position_title)
            .execute()
        )

        if result.data:
            return result.data[0]["id"]

        # Create new position
        result = (
            self.supabase.table("positions")
            .insert({"company_id": company_id, "title": position_title})
            .execute()
        )
        return result.data[0]["id"]

    async def _get_existing_phone_hashes(self, position_id: str) -> List[str]:
        """Get all existing phone hashes for this position to avoid duplicates"""
        result = (
            self.supabase.table("candidates")
            .select("phone_sha256")
            .eq("position_id", position_id)
            .execute()
        )
        return [
            record["phone_sha256"] for record in result.data if record["phone_sha256"]
        ]

    def _build_scraping_task(self, portal_url: str, position_name: str) -> str:
        """Build the task description for Browser-Use agent"""
        return f"""## Cíl
Přihlaš se na {portal_url} pomocí zadaných přihlašovacích údajů.
Vyhledej pozici s názvem "{position_name}", otevři seznam všech kandidátů (interní, neveřejná část).

U každého kandidáta vytěž:
  – first_name
  – last_name
  – email
  – phone

Bezpečnost duplicit:
  1. Před uložením každého kandidáta spočítej `sha256(phone_number)` → hex.
  2. Máš CSV seznam hashů v tajné proměnné `skip_hashes_csv`.
  3. Jestliže hash existuje v seznamu, kandidáta zcela ignoruj.

Výstup:
  Vrať jediný JSON podle `structured_output_json` schématu.
(agent tak splní požadavek "nikdy nezapsat duplicitního kandidáta")."""

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for allowed_domains"""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.netloc

    async def _run_browser_use_task(
        self, task_payload: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Execute Browser-Use task and poll for results"""
        async with httpx.AsyncClient() as client:
            # Start task
            response = await client.post(
                f"{self.browser_use_base_url}/run-task",
                json=task_payload,
                headers={"Authorization": f"Bearer {self.browser_use_api_key}"},
            )
            response.raise_for_status()
            task_data = response.json()
            task_id = task_data["id"]

            # Poll for completion
            while True:
                await asyncio.sleep(5)  # Wait 5 seconds between polls

                status_response = await client.get(
                    f"{self.browser_use_base_url}/task/{task_id}",
                    headers={"Authorization": f"Bearer {self.browser_use_api_key}"},
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                if status_data["status"] == "finished":
                    return status_data.get("output", [])
                elif status_data["status"] == "failed":
                    raise Exception(
                        f"Browser-Use task failed: {status_data.get('error', 'Unknown error')}"
                    )

                # Continue polling if status is "running" or "pending"

    async def _store_candidates(
        self, position_id: str, candidates_data: List[Dict[str, str]], source_url: str
    ) -> Dict[str, int]:
        """Store candidates in database with duplicate prevention"""
        inserted = 0
        skipped = 0

        for candidate in candidates_data:
            try:
                # Prepare candidate record
                candidate_record = {
                    "position_id": position_id,
                    "first_name": candidate.get("first_name"),
                    "last_name": candidate.get("last_name"),
                    "email": candidate.get("email"),
                    "phone": candidate.get("phone"),
                    "source_url": source_url,
                }

                # Try to insert (will fail if duplicate phone_sha256 + position_id)
                self.supabase.table("candidates").insert(candidate_record).execute()
                inserted += 1

            except Exception:
                # Likely a duplicate, count as skipped
                skipped += 1
                continue

        return {"inserted": inserted, "skipped": skipped}
