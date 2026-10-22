import json
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'03_Backend'))
from app.main import app
destination=root/'05_LOS_Integration'/'openapi.generated.json'
destination.write_text(json.dumps(app.openapi(),ensure_ascii=False,indent=2),encoding='utf-8')
print(destination)
