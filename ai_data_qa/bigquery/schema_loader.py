from typing import List, Dict
from ai_data_qa.bigquery.client import BQClient
from ai_data_qa.tests_engine.models import TableSchema, ColumnSchema

class SchemaLoader:
    def __init__(self, bq_client: BQClient):
        self.bq_client = bq_client

    def load_dataset_schema(self, project_id: str, dataset_id: str) -> List[TableSchema]:
        """Loads schema for all tables in a dataset using INFORMATION_SCHEMA."""
        query = f"""
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM
            `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
        ORDER BY
            table_name, ordinal_position
        """
        rows = self.bq_client.execute_query(query)

        tables_dict: Dict[str, List[ColumnSchema]] = {}
        for row in rows:
            table_name = row["table_name"]
            column = ColumnSchema(
                name=row["column_name"],
                data_type=row["data_type"],
                is_nullable=row["is_nullable"] == "YES"
            )
            if table_name not in tables_dict:
                tables_dict[table_name] = []
            tables_dict[table_name].append(column)

        return [
            TableSchema(table_name=table_name, columns=columns)
            for table_name, columns in tables_dict.items()
        ]
