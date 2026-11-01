"""Clip definitions must never become painted brand shapes on Android."""
from pathlib import Path
import tempfile,shutil,subprocess,sys,unittest

class BrandGeometryTest(unittest.TestCase):
    def test_logo_compiler_skips_clip_rect_and_retains_actual_circular_mark(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);tool=work/'android/tools';tool.mkdir(parents=True)
            target=work/'android/app/src/main/java/co/vautomate/customer';target.mkdir(parents=True)
            logos=work/'frontend';logos.mkdir()
            for name in ['brand-long.svg','brand-short.svg']:shutil.copyfile(root/'frontend'/name,logos/name)
            script=tool/'generate-brand-paths.py';shutil.copyfile(root/'android/tools/generate-brand-paths.py',script)
            subprocess.run([sys.executable,str(script)],check=True,capture_output=True)
            output=(target/'BrandPaths.java').read_text()
            self.assertNotIn('p.moveTo(183.160156f,9.492188f)',output)
            self.assertIn('p.moveTo(186.765625f,9.769531f)',output)
            self.assertEqual(output.count('static Path mark'),2)
