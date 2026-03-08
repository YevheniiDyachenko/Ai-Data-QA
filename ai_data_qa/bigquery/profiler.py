from typing import List
from ai_data_qa.bigquery.client import BQClient
from ai_data_qa.tests_engine.models import TableSchema, ProfilingResult
from ai_data_qa.utils.logger import logger

class Profiler:
    def __init__(self, bq_client: BQClient):
        self.bq_client = bq_client

    def profile_table(self, project_id: str, dataset_id: str, table_schema: TableSchema) -> List[ProfilingResult]:
        """Profiles a table by computing row_count, null_count, and distinct_count for each column."""
        table_name = table_schema.table_name
        full_table_path = f"`{project_id}.{dataset_id}.{table_name}`"

        results = []

        # Row count for the table
        row_count_query = f"SELECT COUNT(*) as row_count FROM {full_table_path}"
        try:
            row_count_res = self.bq_client.execute_query(row_count_query)
            total_rows = row_count_res[0]["row_count"]
        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            return []

        for column in table_schema.columns:
            col_name = column.name
            profile_query = f"""
            SELECT
                COUNTIF({col_name} IS NULL) as null_count,
                COUNT(DISTINCT {col_name}) as distinct_count
            FROM {full_table_path}
            """
            try:
                profile_res = self.bq_client.execute_query(profile_query)
                results.append(ProfilingResult(
                    table_name=table_name,
                    column_name=col_name,
                    row_count=total_rows,
                    null_count=profile_res[0]["null_count"],
                    distinct_count=profile_res[0]["distinct_count"]
                ))
            except Exception as e:
                logger.warning(f"Failed to profile column {col_name} in {table_name}: {e}")

        return results
