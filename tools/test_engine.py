from pathlib import Path
import json,sys,unittest
project=Path(__file__).resolve().parents[1]
suite=unittest.defaultTestLoader.discover(str(project/'tests'),pattern='test_*.py')
result=unittest.TextTestRunner(verbosity=2).run(suite)
evidence=project/'evidence';evidence.mkdir(exist_ok=True)
(evidence/'engine-results.json').write_text(json.dumps({'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'Isolated engine and simulated adapter. No live HAOS connection.'},indent=2),encoding='utf-8')
sys.exit(0 if result.wasSuccessful() else 1)
