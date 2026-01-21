"""UI utilities for the CLI."""

from rich.console import Console
from rich.table import Table

console = Console()

def print_table_schema(table_name: str, table_obj):
    """Print high-level schema of a database table."""
    schema_table = Table(title=f"Schema for {table_name}", show_header=True, header_style="bold magenta")
    schema_table.add_column("CID", justify="right")
    schema_table.add_column("Name")
    schema_table.add_column("Type")
    schema_table.add_column("NOTNULL")
    schema_table.add_column("PK", justify="right")

    for col in table_obj.columns:
        is_pk = col.name in table_obj.pks
        schema_table.add_row(
            str(col.cid),
            col.name,
            col.type,
            "✓" if col.notnull else "",
            "✓" if is_pk else ""
        )
    console.print(schema_table)

def print_sample_data(table_name: str, table_obj, limit: int = 5):
    """Print sample rows from a database table."""
    rows = list(table_obj.rows_where(limit=limit))
    if not rows:
        console.print(f"[yellow]No data in {table_name}[/]")
        return

    data_table = Table(title=f"Sample data from {table_name} (LIMIT {limit})", show_header=True, header_style="bold green")
    
    all_cols = list(rows[0].keys())
    # Adjust display columns for readability
    if table_name == "documents":
        display_cols = ["id", "relative_path", "file_type", "title", "category", "category_confidence"]
    else:
        display_cols = all_cols[:8]
    
    for col_name in display_cols:
        data_table.add_column(col_name, overflow="ellipsis")
    
    for row in rows:
        data_table.add_row(*[str(row.get(c, "")) for c in display_cols])
    
    console.print(data_table)
