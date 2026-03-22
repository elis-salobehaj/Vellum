"""Dagster service — trigger ingestion assets via the Dagster GraphQL API.

Replaces kfp_service.py. The INGESTION_MODE setting now defaults to 'dagster'
for pipeline-triggered runs, or 'direct' for the synchronous in-process path.
"""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import logger

# GraphQL mutation to launch all assets in the ingestion group
_LAUNCH_MUTATION = """
mutation LaunchIngestion {
  launchPipelineExecution(
    executionParams: {
      selector: {
        repositoryLocationName: "dagster_vellum"
        repositoryName: "__repository__"
        pipelineName: "__ASSET_JOB"
      }
      runConfigData: {}
      mode: "default"
    }
  ) {
    __typename
    ... on LaunchRunSuccess {
      run {
        runId
      }
    }
    ... on PythonError {
      message
    }
    ... on PipelineNotFoundError {
      message
    }
  }
}
"""


class DagsterService:
    def __init__(self) -> None:
        self.graphql_url = settings.DAGSTER_GRAPHQL_URL

    async def trigger_ingestion(self) -> dict:
        """Trigger the ingestion asset job via the Dagster GraphQL API."""
        logger.info("dagster_trigger_ingestion", url=self.graphql_url)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.graphql_url,
                    json={"query": _LAUNCH_MUTATION},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

            payload = data.get("data", {}).get("launchPipelineExecution", {})
            typename = payload.get("__typename", "")

            if typename == "LaunchRunSuccess":
                run_id = payload["run"]["runId"]
                logger.info("dagster_trigger_success", run_id=run_id)
                return {
                    "status": "success",
                    "run_id": run_id,
                    "message": f"Dagster ingestion job launched. Run ID: {run_id}",
                }

            message = payload.get("message", str(payload))
            logger.error("dagster_trigger_failed", typename=typename, message=message)
            return {"status": "error", "message": message}

        except Exception as exc:
            logger.error("dagster_trigger_exception", error=str(exc))
            return {"status": "error", "message": str(exc)}


dagster_service = DagsterService()
