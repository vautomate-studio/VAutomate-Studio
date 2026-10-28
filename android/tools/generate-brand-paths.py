"""Compile the official SVG paths into native Canvas geometry without a drawable loader."""
from pathlib import Path
import re, xml.etree.ElementTree as ET

project = Path(__file__).resolve().parents[1]
logos = project.parent / 'VAutomate'
if not logos.exists(): logos = project / 'app/src/main/assets/vautomate-customer'
methods = []
def number(v):
    s = f'{v:.6f}'.rstrip('0').rstrip('.')
    return (s if '.' in s else s + '.0') + 'f'
def convert(filename, name, split=False):
    root = ET.parse(logos / filename).getroot()
    ox, oy, _, _ = map(float, root.get('viewBox').split())
    leaves = []
    def visit(node, tx=0, ty=0):
        transform = node.get('transform')
        if transform:
            m = re.fullmatch(r'translate\(\s*([\d.eE+-]+)[ ,]+([\d.eE+-]+)\s*\)', transform)
            assert m, transform
            tx += float(m[1]); ty += float(m[2])
        if node.tag.rsplit('}', 1)[-1] == 'path':
            tokens = re.findall(r'[MLCZ]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', node.get('d'))
            assert not set(re.findall('[A-Za-z]', node.get('d'))) - set('MLCZ')
            lines = []; i = 0
            while i < len(tokens):
                command = tokens[i]; i += 1
                if command == 'Z': lines.append('p.close();'); continue
                count = {'M':2, 'L':2, 'C':6}[command]
                values = list(map(float, tokens[i:i+count])); i += count
                values = [v + (tx-ox if index % 2 == 0 else ty-oy) for index, v in enumerate(values)]
                lines.append('p.' + {'M':'moveTo','L':'lineTo','C':'cubicTo'}[command] + '(' + ','.join(map(number, values)) + ');')
            leaves.append(lines)
        for child in node: visit(child, tx, ty)
    visit(root)
    if split:
        for i, leaf in enumerate(leaves):
            methods.append('static Path '+name+str(i)+'(){Path p=new Path();\n'+'\n'.join(leaf)+'\nreturn p;}')
    else:
        methods.append('static Path '+name+'(){Path p=new Path();\n'+'\n'.join(line for leaf in leaves for line in leaf)+'\nreturn p;}')
convert('brand-short.svg', 'mark', True)
convert('brand-long.svg', 'wordmark')
target = project / 'app/src/main/java/co/vautomate/home/BrandPaths.java'
target.write_text('package co.vautomate.customer;\nimport android.graphics.Path;\n/** Generated from the official VAutomate SVG files. */\nfinal class BrandPaths {\n'+'\n'.join(methods)+'\n}\n', encoding='utf-8')
print('Compiled official short and long logos to native Canvas paths.')
