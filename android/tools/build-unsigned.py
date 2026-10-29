"""Build a VAutomate APK using official JDK/Android SDK tools, without Gradle."""
from pathlib import Path
import argparse,subprocess,zipfile,datetime,os,hashlib,json
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--java-home',type=Path,required=True,help='JDK 17 installation root')
parser.add_argument('--android-jar',type=Path,required=True,help='SDK Platform 36 android.jar')
parser.add_argument('--build-tools',type=Path,required=True,help='SDK Build-Tools 35.0.0 folder')
parser.add_argument('--output',type=Path,default=Path('VAutomate-aligned-unsigned.apk'))
parser.add_argument('--r8-jar',type=Path,help='Compatible current R8 jar when the SDK bundled D8 predates Kotlin 2.1')
args=parser.parse_args();project=Path(__file__).resolve().parents[1]
build=project/'build'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');build.mkdir(parents=True,exist_ok=True)
generated=build/'generated';generated.mkdir();classes=build/'classes';classes.mkdir();dex=build/'dex';dex.mkdir()
jdk=args.java_home/'bin';android=args.android_jar.resolve();tools=args.build_tools.resolve()
def exe(folder,name):return folder/(name+'.exe' if (folder/(name+'.exe')).exists() else name)
def run(values):subprocess.run([str(value) for value in values],check=True)
run([exe(tools,'aapt2'),'compile','--dir',project/'app/src/main/res','-o',build/'resources.zip'])
run([exe(tools,'aapt2'),'link','-o',build/'resources.apk','--manifest',project/'app/src/main/AndroidManifest.xml','-I',android,'--java',generated,'--extra-packages','androidx.startup:androidx.tracing','--min-sdk-version','31','--target-sdk-version','36','--version-code','8','--version-name','0.4.0-alpha.2','-A',project/'app/src/main/assets',build/'resources.zip'])
sources=list((project/'app/src/main/java').rglob('*.java'))+list(generated.rglob('*.java'))
libraries=sorted((project/'vendor').glob('*.jar'))
lock=json.loads((project/'vendor/dependencies.json').read_text(encoding='utf-8'))
for item in lock:
 file=project/'vendor'/(item['name']+'-'+item['version']+'.jar');assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256'],'Dependency hash mismatch'
arguments=['-encoding','UTF-8','--release','8','-classpath',os.pathsep.join([str(android)]+[str(p) for p in libraries]),'-d',str(classes)]+[str(file) for file in sources]
argfile=build/'javac.args';argfile.write_text('\n'.join('"'+value.replace('\\','/')+'"' for value in arguments),encoding='utf-8')
run([exe(jdk,'javac'),'@'+str(argfile)])
with zipfile.ZipFile(build/'classes.jar','w',zipfile.ZIP_DEFLATED) as archive:
 for file in classes.rglob('*.class'):archive.write(file,file.relative_to(classes).as_posix())
run([exe(jdk,'java'),'-cp',args.r8_jar or tools/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','31','--lib',android,'--output',dex,build/'classes.jar',*libraries])
with zipfile.ZipFile(build/'resources.apk') as original,zipfile.ZipFile(build/'unsigned.apk','w',zipfile.ZIP_DEFLATED) as archive:
 for item in original.infolist():archive.writestr(item,original.read(item.filename))
 for file in dex.glob('*.dex'):archive.write(file,file.name)
 existing=set(archive.namelist())
 for library in libraries:
  with zipfile.ZipFile(library) as resources:
   for name in resources.namelist():
    if name.endswith('/') or name.endswith('.class') or name in existing or name.upper().endswith(('.SF','.RSA','.DSA')) or name=='META-INF/MANIFEST.MF':continue
    archive.writestr(name,resources.read(name));existing.add(name)
args.output.parent.mkdir(parents=True,exist_ok=True)
run([exe(tools,'zipalign'),'-f','-p','4',build/'unsigned.apk',args.output])
print('Aligned APK built. Sign it with your own Android signing key:',args.output)
