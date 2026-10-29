"""Check native URL policy with a plain JDK; no phone or Android runtime implied."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser=argparse.ArgumentParser()
parser.add_argument('--java-home',type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
def binary(name):
    if args.java_home:
        path=args.java_home/'bin'/name
        if path.with_suffix('.exe').is_file():return str(path.with_suffix('.exe'))
        return str(path)
    value=shutil.which(name)
    if not value:raise SystemExit('A JDK is required for the native policy check.')
    return value
source=root/'android/app/src/main/java/co/vautomate/customer'
with tempfile.TemporaryDirectory(prefix='vautomate-native-policy-') as folder:
    subprocess.run([binary('javac'),'-encoding','UTF-8','-d',folder,str(source/'EndpointPolicy.java'),str(source/'StudioReadOnlyPolicy.java'),str(root/'tests/NativePolicyTest.java')],check=True)
    subprocess.run([binary('java'),'-cp',folder,'co.vautomate.customer.NativePolicyTest'],check=True)
