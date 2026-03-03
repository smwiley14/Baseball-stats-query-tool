from pydantic import BaseModel
from pathlib import Path
import re
import yaml

# from backend.database.db_connect import DBConfig
# from backend.database.params import DBParams

class ColumnInfo(BaseModel):
    name: str
    description: str
    type: str
    is_primary_key: bool
    is_nullable: bool
    foreign_keys: list[dict]

    @staticmethod
    def _extract_type(column: dict) -> str:
        """Extract the type of a column from the database."""
        column_type = str(column["type"])
        return column_type if column_type != "NULL" else "USER-DEFINED"


class TableInfo(BaseModel):
    """Information about a database table."""

    name: str
    schema_name: str
    description: str
    primary_keys: list[str]
    foreign_keys: list[dict]
    columns: list[ColumnInfo]

    @classmethod
    def from_inspector(cls, inspector, table, schema) -> "TableInfo":
        """Create TableInfo from SQLAlchemy inspector."""
        columns = inspector.get_columns(table, schema=schema)

        primary_keys = inspector.get_pk_constraint(table, schema=schema)

        foreign_keys = inspector.get_foreign_keys(table, schema=schema)

        column_info = [
            ColumnInfo(
                name=column["name"],
                description=column.get("comment", "") or "",
                type=ColumnInfo._extract_type(column),
                is_primary_key=column["name"]
                in primary_keys.get("constrained_columns", []),
                is_nullable=column["nullable"],
                foreign_keys=[
                    {
                        "referred_table": fk.get("referred_table"),
                        "referred_schema": fk.get("referred_schema"),
                        "referred_columns": fk.get("referred_columns"),
                        "name": fk.get("name"),
                    }
                    for fk in foreign_keys
                    if column["name"] in fk.get("constrained_columns", [])
                ],
            )
            for column in columns
        ]

        return cls(
            name=table,
            schema_name=schema,
            description=(
                inspector.get_table_comment(table, schema=schema).get("text", "") or ""
            ),
            primary_keys=primary_keys.get("constrained_columns", []),
            foreign_keys=[
                {
                    "constrained_columns": fk.get("constrained_columns", []),
                    "referred_table": fk.get("referred_table"),
                    "referred_schema": fk.get("referred_schema"),
                    "referred_columns": fk.get("referred_columns"),
                    "name": fk.get("name"),
                }
                for fk in foreign_keys
            ],
            columns=column_info,
        )

    def format_context(self) -> str:
        """Format table information as a string for context retrieval."""
        context = f"TABLE: {self.name}\n"
        if self.description:
            context += f"DESCRIPTION: {self.description}\n"

        if self.primary_keys:
            context += f"PRIMARY KEYS: {', '.join(self.primary_keys)}\n"

        if self.foreign_keys:
            context += "FOREIGN KEYS:\n"
            for fk in self.foreign_keys:
                constrained = ", ".join(fk["constrained_columns"])
                referred = ", ".join(fk["referred_columns"])
                context += (
                    f"  - {constrained} -> "
                    f"{fk['referred_schema']}.{fk['referred_table']}.{referred}\n"
                )

        context += "COLUMNS:\n"
        for column in self.columns:
            # Format column type, nullability, and description
            is_nullable = "NULL" if column.is_nullable else "NOT NULL"
            if column.description:
                context += (
                    f"  - {column.name} ({column.type}, {is_nullable}): "
                    f"{column.description}\n"
                )
            else:
                context += (
                    f"  - {column.name} ({column.type}, {is_nullable})\n"
                )
        # print(context)
        return context

class SchemaInfo(BaseModel):
    """Information about a database schema."""

    name: str
    tables: dict[str, TableInfo]

    def format_context(self) -> str:
        """Format schema information as a string for context retrieval."""
        context = f"SCHEMA: {self.name}\n\n"
        for table_info in self.tables.values():
            context += table_info.format_context() + "\n\n"
        return context


class DatabaseInfo(BaseModel):
    """Information about a database."""

    name: str
    schemas: dict[str, SchemaInfo]

    def format_context(self) -> str:
        """Format database information as a string for context retrieval."""
        context = f"DATABASE: {self.name}\n\n"
        for schema_info in self.schemas.values():
            context += schema_info.format_context()
        return context
# table_info = TableInfo.from_inspector(inspector, table, schema)
# print(table_info.format_context())

class DataDictionary(BaseModel):
    """Main data dictionary containing all database information."""

    databases: dict[str, DatabaseInfo] 

    @classmethod
    def from_inspector(
        cls,
        inspector,
        database_schema,
    ) -> "DataDictionary":
        """Create DataDictionary from SQLAlchemy inspector."""
        databases = {}

        for database_name, schemas in database_schema.items():
            schema_dict = {}
            # print(database_name, schemas)
            for schema_name, tables in schemas.items():
                table_dict = {}
                for table_name in tables:
                    table_info = TableInfo.from_inspector(
                        inspector, table_name, schema_name
                    )

                    table_dict[table_name] = table_info
                    # print(table_info, "\n")
                schema_dict[schema_name] = SchemaInfo(
                    name=schema_name, tables=table_dict
                )

            databases[database_name] = DatabaseInfo(
                name=database_name, schemas=schema_dict
            )
        
        # Create and return DataDictionary instance with the populated databases
        return cls(databases=databases)
    
    @classmethod
    def from_db_connector(cls, db_connector) -> "DataDictionary":
        """
        Create DataDictionary from a DBConnector instance.
        
        This is a convenience method that extracts inspector and schema
        from the DBConnector automatically.
        
        Args:
            db_connector: DBConnector instance
            
        Returns:
            DataDictionary populated from the database
        """
        return cls.from_inspector(
            inspector=db_connector.get_inspector(),
            database_schema=db_connector.get_schema()
        )

    def format_context(self) -> str:
        """Format all schema information as a string for context retrieval."""
        context = ""
        for database_info in self.databases.values():
            context += database_info.format_context()
        return context



    @classmethod
    def _parse_flat_column_line(cls, line: str) -> ColumnInfo:
        """Parse a column line like 'player_id (VARCHAR(10), NOT NULL)' or with description."""
        # Match "name (TYPE, NULL|NOT NULL)" optionally followed by ": description"
        match = re.match(r"^\s*-\s*(\w+)\s*\(([^,]+),\s*(NULL|NOT NULL)\)(?:\s*:\s*(.*))?$", line.strip())
        if not match:
            # Fallback: accept "name (TYPE, NULL)" without leading " - "
            match = re.match(r"^(\w+)\s*\(([^,]+),\s*(NULL|NOT NULL)\)(?:\s*:\s*(.*))?$", line.strip())
        if not match:
            return ColumnInfo(
                name="unknown",
                description="",
                type="TEXT",
                is_primary_key=False,
                is_nullable=True,
                foreign_keys=[],
            )
        name, col_type, null_str, desc = match.groups()
        return ColumnInfo(
            name=name,
            description=(desc or "").strip(),
            type=col_type.strip(),
            is_primary_key=False,  # set from primary_keys list
            is_nullable=null_str.strip().upper() == "NULL",
            foreign_keys=[],
        )

    @classmethod
    def _parse_flat_foreign_key(cls, fk_str: str) -> dict | None:
        """Parse 'col -> schema.table.ref_col' into foreign key dict."""
        if "->" not in fk_str:
            return None
        left, right = fk_str.split("->", 1)
        constrained_col = left.strip().strip("- ").strip()
        ref_part = right.strip()
        parts = ref_part.split(".")
        if len(parts) != 3:
            return None
        ref_schema, ref_table, ref_col = parts
        return {
            "constrained_columns": [constrained_col],
            "referred_table": ref_table.strip(),
            "referred_schema": ref_schema.strip(),
            "referred_columns": [ref_col.strip()],
            "name": f"fk_{constrained_col}_{ref_table}",
        }

    @classmethod
    def _table_info_from_flat(cls, table_name: str, schema_name: str, flat: dict) -> TableInfo:
        """Build TableInfo from a flat table block (TABLE, PRIMARY KEYS, COLUMNS, etc.)."""
        primary_keys_raw = flat.get("PRIMARY KEYS") or flat.get("primary_keys")
        if isinstance(primary_keys_raw, str):
            primary_keys = [p.strip() for p in primary_keys_raw.split(",")]
        elif isinstance(primary_keys_raw, list):
            primary_keys = list(primary_keys_raw)
        else:
            primary_keys = []

        fk_strs = flat.get("FOREIGN KEYS") or flat.get("foreign_keys") or []
        foreign_keys = []
        for item in fk_strs:
            if isinstance(item, str):
                fk = cls._parse_flat_foreign_key(item)
                if fk:
                    foreign_keys.append(fk)
            elif isinstance(item, dict):
                foreign_keys.append(item)

        column_lines = flat.get("COLUMNS") or flat.get("columns") or []
        columns = []
        for line in column_lines:
            if isinstance(line, str):
                col = cls._parse_flat_column_line(line)
            else:
                col = ColumnInfo(
                    name=str(line.get("name", "unknown")),
                    description=str(line.get("description", "")),
                    type=str(line.get("type", "TEXT")),
                    is_primary_key=line.get("name") in primary_keys,
                    is_nullable=line.get("is_nullable", True),
                    foreign_keys=[],
                )
            col.is_primary_key = col.name in primary_keys
            col.foreign_keys = [
                fk for fk in foreign_keys
                if fk.get("constrained_columns") and col.name in fk["constrained_columns"]
            ]
            columns.append(col)

        return TableInfo(
            name=table_name,
            schema_name=schema_name,
            description=(flat.get("DESCRIPTION") or flat.get("description") or ""),
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            columns=columns,
        )

    @classmethod
    def _load_flat_db_dict(cls, file_path: Path) -> "DataDictionary":
        """Load the flat db_dict.yml format (DATABASE, SCHEMA, repeated TABLE/PRIMARY KEYS/COLUMNS)."""
        with open(file_path) as f:
            content = f.read()

        parts = re.split(r"\n\nTABLE:\s*", content, flags=re.IGNORECASE)
        if len(parts) < 2:
            return cls(databases={})

        header = parts[0].strip()
        try:
            header_data = yaml.safe_load(header) or {}
        except Exception:
            header_data = {}
        database_name = header_data.get("DATABASE") or header_data.get("database") or "retrosheet"
        schema_name = header_data.get("SCHEMA") or header_data.get("schema") or "public"

        tables: dict[str, TableInfo] = {}
        for block in parts[1:]:
            block_yaml = "TABLE: " + block.strip()
            try:
                flat = yaml.safe_load(block_yaml) or {}
            except Exception:
                continue
            table_name = flat.get("TABLE")
            if not table_name:
                continue
            table_info = cls._table_info_from_flat(str(table_name), schema_name, flat)
            tables[table_info.name] = table_info

        schema_info = SchemaInfo(name=schema_name, tables=tables)
        database_info = DatabaseInfo(name=database_name, schemas={schema_name: schema_info})
        return cls(databases={database_name: database_info})

    @classmethod
    def load(
        cls, file_path: Path | str | None = None
    ) -> "DataDictionary":
        """Load data dictionary from a YAML file. Supports both 'databases' structure and flat db_dict format."""
        _PROJECT_ROOT = Path(__file__).parent.parent.parent
        if file_path is None:
            file_path = _PROJECT_ROOT  / "configs" / "db_dict.yml"
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"Warning: Data dictionary file not found: {file_path}. Using empty dictionary.")
            return cls(databases={})

        with open(file_path) as f:
            raw_data = yaml.safe_load(f)

        if raw_data is None:
            return cls(databases={})

        if "databases" in raw_data:
            return cls(**raw_data)

        # Flat format: DATABASE, SCHEMA, TABLE, PRIMARY KEYS, COLUMNS (repeated per table)
        if "DATABASE" in raw_data or "TABLE" in raw_data:
            return cls._load_flat_db_dict(file_path)

        print(
            f"Warning: YAML file {file_path} has unexpected structure. "
            f"Expected 'databases' or flat keys but found: {list(raw_data.keys())[:5]}. "
            f"Using empty dictionary. Use from_inspector() to populate from database."
        )
        return cls(databases={})
