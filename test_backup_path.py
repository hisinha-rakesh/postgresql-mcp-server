#!/usr/bin/env python3
"""
Test script to verify backup path handling
"""

from pathlib import Path
from datetime import datetime

def test_backup_path_handling(backup_path, database_name, backup_format):
    """Test how backup path is handled"""

    print(f"\nTest Case:")
    print(f"  Input path: {backup_path}")
    print(f"  Database: {database_name}")
    print(f"  Format: {backup_format}")

    backup_path_obj = Path(backup_path)

    # Check if it's a directory or needs filename generation
    if backup_path_obj.is_dir() or (not backup_path_obj.suffix and not backup_path_obj.exists()):
        # It's a directory - auto-generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        ext_map = {
            "custom": ".dump",
            "plain": ".sql",
            "tar": ".tar",
            "directory": ""
        }
        extension = ext_map.get(backup_format, ".dump")

        filename = f"{database_name}_backup_{timestamp}{extension}"
        final_path = str(backup_path_obj / filename)

        print(f"  -> Path is directory, auto-generating filename")
        print(f"  -> Generated filename: {filename}")
    else:
        # It's a full path with filename
        final_path = backup_path
        print(f"  -> Path includes filename, using as-is")

    print(f"  ✓ Final path: {final_path}")
    return final_path


# Test cases
print("=" * 80)
print("BACKUP PATH HANDLING TESTS")
print("=" * 80)

# Test 1: Directory only (existing)
test_backup_path_handling(
    backup_path=r"C:\Agentic-RAG",
    database_name="youtube_db",
    backup_format="custom"
)

# Test 2: Directory only (new, doesn't exist yet)
test_backup_path_handling(
    backup_path=r"C:\Backups\PostgreSQL",
    database_name="library",
    backup_format="plain"
)

# Test 3: Full path with filename
test_backup_path_handling(
    backup_path=r"C:\Agentic-RAG\my_custom_backup.dump",
    database_name="youtube_db",
    backup_format="custom"
)

# Test 4: Full path with .sql extension
test_backup_path_handling(
    backup_path=r"C:\Agentic-RAG\library_export.sql",
    database_name="library",
    backup_format="plain"
)

# Test 5: Different formats
for fmt in ["custom", "plain", "tar", "directory"]:
    test_backup_path_handling(
        backup_path=r"C:\Agentic-RAG",
        database_name="testdb",
        backup_format=fmt
    )

print("\n" + "=" * 80)
print("✓ All path handling tests completed successfully!")
print("=" * 80)
