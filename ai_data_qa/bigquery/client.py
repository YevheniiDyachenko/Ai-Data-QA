from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery
from typing import Any, Dict, List

from ai_data_qa.errors import ExecutionError, RetryableExecutionError
from ai_data_qa.utils.logger import logger

_TRANSIENT_ERRORS = (
    gcp_exceptions.TooManyRequests,
    gcp_exceptions.InternalServerError,
    gcp_exceptions.BadGateway,
    gcp_exceptions.ServiceUnavailable,
    gcp_exceptions.GatewayTimeout,
)


class BQClient:
    def __init__(self, project_id: str, location: str = "US"):
        self.project_id = project_id
        self.location = location
        self.client = bigquery.Client(project=project_id)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns results as a list of dictionaries."""
        logger.info(f"Executing query: {query}")
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [dict(row) for row in results]
        except _TRANSIENT_ERRORS as exc:
            logger.warning(f"Transient BigQuery error: {exc}")
            raise RetryableExecutionError(
                "Transient BigQuery error",
                provider="bigquery",
                reason=str(exc),
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Error executing query: {exc}")
            raise ExecutionError("BigQuery query execution failed", provider="bigquery", reason=str(exc)) from exc

    def get_table_schema(self, dataset_id: str, table_id: str) -> List[Dict[str, Any]]:
        """Retrieves schema for a specific table."""
        dataset_ref = self.client.dataset(dataset_id)
        table_ref = dataset_ref.table(table_id)
        table = self.client.get_table(table_ref)
        return [{"name": field.name, "type": field.field_type, "mode": field.mode} for field in table.schema]
