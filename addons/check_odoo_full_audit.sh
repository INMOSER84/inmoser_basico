#!/bin/bash
# check_odoo_full_audit.sh
# Auditoría 100 % completa de vistas XML en Odoo 17 Community
# Uso: ./check_odoo_full_audit.sh [ruta_módulos] [nombre_db] [odoo.conf]

MODULE_DIR="${1:-./}"            # carpeta que contiene los módulos
DB_NAME="${2:-your_database}"    # base de datos donde están instalados los módulos
ODOO_CONFIG="${3:-/etc/odoo/odoo.conf}"  # archivo de configuración de Odoo

echo "🔍 AUDITORÍA 100 % VISTAS ODOO 17 COMMUNITY"
echo "Ruta módulos : $MODULE_DIR"
echo "Base de datos: $DB_NAME"
echo "Config Odoo  : $ODOO_CONFIG"
echo "--------------------------------------------------"

# 1️⃣  Fase rápida Bash (sintaxis XML, tags abiertos, deprecados)
echo "🧪 Fase 1: validación rápida Bash..."
FILES=$(find "$MODULE_DIR" -type f \( -path "*/views/*.xml" -o -path "*/data/*.xml" -o -path "*/reports/*.xml" \))

for f in $FILES; do
    echo "📄 $f"
    xmllint --noout "$f" 2>/tmp/xerr && rm -f /tmp/xerr || { echo "❌ XML malformado"; cat /tmp/xerr; }
    grep -nE '<record[^>]*/>' "$f" && echo "⚠️  record vacío de cierre automático"
    grep -nE '<field[^>]*/>' "$f" && echo "⚠️  field vacío de cierre automático"
    grep -nE 'attrs=|states=' "$f" && echo "⚠️  attrs/states deprecados"
    grep -nE 'invisible=|readonly=|required=' "$f" | grep -v '"' && echo "⚠️  atributos sin comillas"
done

# 2️⃣  Fase profunda Python (100 % cobertura)
echo "--------------------------------------------------"
echo "🧠 Fase 2: auditoría profunda Python (+Odoo ORM)..."

python3 <<EOF_PY
import os, sys, glob, re
from lxml import etree
from collections import defaultdict

# Inicializar Odoo
import odoo
from odoo import api, registry, SUPERUSER_ID
from odoo.tools import config, safe_eval

config.parse_config(['-c', '$ODOO_CONFIG'])
cr = registry('$DB_NAME').cursor()
env = api.Environment(cr, SUPERUSER_ID, {})

XML_FILES = []
for root, _, files in os.walk('$MODULE_DIR'):
    for f in files:
        if f.lower().endswith('.xml'):
            XML_FILES.append(os.path.join(root, f))

errors = []
view_keys = defaultdict(list)   # (model, type) -> [id]
all_ids = set()                 # para detectar duplicados globales

def ref(xml_id):
    return env.ref(xml_id, raise_if_not_found=False)

for path in XML_FILES:
    try:
        tree = etree.parse(path)
    except Exception as e:
        errors.append(f"{path}: XML malformado → {e}")
        continue

    # ---------- <record model="ir.ui.view"> ----------
    for rec in tree.xpath("//record[@model='ir.ui.view']"):
        xml_id = rec.get('id')
        if xml_id:
            if xml_id in all_ids:
                errors.append(f"{path}: ID duplicada → {xml_id}")
            all_ids.add(xml_id)

        model_f = rec.xpath(".//field[@name='model']")
        if not model_f:
            errors.append(f"{path}: vista sin model → id={xml_id}")
            continue
        model = model_f[0].text
        if not env.registry.has(model):
            errors.append(f"{path}: modelo inexistente → {model} (id={xml_id})")

        # inherit_id
        inh = rec.xpath(".//field[@name='inherit_id']")
        if inh:
            ref_txt = inh[0].get('ref') or inh[0].text
            if ref_txt and not ref(ref_txt):
                errors.append(f"{path}: inherit_id inválido → {ref_txt} (id={xml_id})")

        # type
        type_f = rec.xpath(".//field[@name='type']")
        vtype = type_f[0].text if type_f else 'form'
        view_keys[(model, vtype)].append(xml_id)

        # groups
        grp = rec.xpath(".//field[@name='groups_id']")
        for g in grp:
            for xmlg in re.findall(r'[\w\.]+', g.text or ''):
                if not ref(xmlg):
                    errors.append(f"{path}: grupo inexistente → {xmlg}")

    # ---------- <record model="ir.model.fields"> ----------
    for rec in tree.xpath("//record[@model='ir.model.fields']"):
        model = rec.xpath(".//field[@name='model']")[0].text
        if not env.registry.has(model):
            errors.append(f"{path}: modelo en ir.model.fields inexistente → {model}")
        comodel = rec.xpath(".//field[@name='comodel_name']")
        if comodel:
            cm = comodel[0].text
            if not env.registry.has(cm):
                errors.append(f"{path}: comodel_name inexistente → {cm}")

    # ---------- <template> ----------
    for tpl in tree.xpath("//template"):
        tid = tpl.get('id')
        if not tid:
            errors.append(f"{path}: template sin id")
        for tc in tpl.xpath(".//t-call"):
            ref_call = (tc.text or '').strip()
            if ref_call and not ref(ref_call):
                errors.append(f"{path}: t-call a template inexistente → {ref_call}")

    # ---------- domain / context / eval ----------
    for fld in tree.xpath(".//field[@domain]|.//field[@context]|.//field[@eval]"):
        for attr in ('domain','context','eval'):
            val = fld.get(attr)
            if val:
                try:
                    safe_eval(val)
                except Exception as e:
                    errors.append(f"{path}: {attr} inválido → {val[:50]}… ({e})")

# ---------- duplicados (model,type) ----------
for (m, t), ids in view_keys.items():
    if len(ids) > 1:
        errors.append(f"Vistas duplicadas (model={m}, type={t}) → ids={ids}")

# ---------- resumen ----------
if errors:
    print("\n".join(f"❌ {e}" for e in errors))
else:
    print("✅ No se detectaron errores que rompan vistas.")
print(f"📊 Total errores: {len(errors)}")
cr.close()
EOF_PY

echo "--------------------------------------------------"
echo "✅ Auditoría total finalizada."

