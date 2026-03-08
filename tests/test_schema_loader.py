import pytest
from unittest.mock import MagicMock
from ai_data_qa.bigquery.schema_loader import SchemaLoader
from ai_data_qa.bigquery.client import BQClient

def test_load_dataset_schema():
    mock_bq_client = MagicMock(spec=BQClient)
    mock_bq_client.execute_query.return_value = [
        {"table_name": "users", "column_name": "id", "data_type": "INT64", "is_nullable": "NO"},
        {"table_name": "users", "column_name": "email", "data_type": "STRING", "is_nullable": "YES"},
        {"table_name": "orders", "column_name": "order_id", "data_type": "INT64", "is_nullable": "NO"},
    ]

    loader = SchemaLoader(mock_bq_client)
    schemas = loader.load_dataset_schema("test-project", "test-dataset")

    assert len(schemas) == 2
    users_schema = next(s for s in schemas if s.table_name == "users")
    assert len(users_schema.columns) == 2
    assert users_schema.columns[0].name == "id"
    assert users_schema.columns[0].is_nullable is False
    assert users_schema.columns[1].name == "email"
    assert users_schema.columns[1].is_nullable is True

    orders_schema = next(s for s in schemas if s.table_name == "orders")
    assert len(orders_schema.columns) == 1
    assert orders_schema.columns[0].name == "order_id"
