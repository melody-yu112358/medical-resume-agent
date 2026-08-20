"""Run the local demo without installing the package first."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent / "src"))

from medical_resume_agent.api import create_app


create_app().run(host="127.0.0.1", port=5001, debug=True)
