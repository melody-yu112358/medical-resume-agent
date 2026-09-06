#!/usr/bin/env python3
"""Start the standalone read-only Career Map pilot on loopback."""
import argparse
from pathlib import Path
import sys
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from medical_career_agent.career_map_viewer import create_viewer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / ".local/career-map.sqlite")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    try:
        app = create_viewer(args.database)
    except sqlite3.Error:
        parser.exit(1, "无法读取知识库。请确认 SQLite 文件有效，并运行导入脚本。\n")
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")
    print(f"职业知识试用台：http://127.0.0.1:{args.port}  （Ctrl+C 停止）", flush=True)
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
