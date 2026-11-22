#!/usr/bin/env node
// Builds the VRMS data diagrams from welinc-backend-vrms/prisma/schema.prisma, so they never drift
// from the schema by hand:
//   4.5.2-physical-schema.puml  every table, column, SQL type, key and enum (PlantUML IE diagram)
//   4.5.1-erd.puml              the logical ERD (keys plus the main attributes, crow's foot notation)
//
//   node docs/context/vrms/diagrams/generate-erd.mjs [path/to/schema.prisma]
// Then render the .puml files with PlantUML (see README in this folder).

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../..');
const schemaFile = process.argv[2] ?? path.join(root, 'welinc-backend-vrms/prisma/schema.prisma');
const src = readFileSync(schemaFile, 'utf8').replace(/\/\/[^\n]*/g, '');

const blocks = [...src.matchAll(/^(model|enum)\s+(\w+)\s*\{([\s\S]*?)^\}/gm)];
const enums = new Map();
const models = new Map();
for (const [, kind, name, body] of blocks) {
  const lines = body.split('\n').map((l) => l.trim()).filter(Boolean);
  if (kind === 'enum') enums.set(name, lines.filter((l) => !l.startsWith('@@')));
  else models.set(name, lines);
}

const BASE = { Int: 'integer', BigInt: 'bigint', Boolean: 'boolean', Float: 'double precision', Json: 'jsonb', Decimal: 'decimal(65,30)', DateTime: 'timestamp(3)', String: 'text', Bytes: 'bytea' };
const DB = { Uuid: 'uuid', Text: 'text', SmallInt: 'smallint', Integer: 'integer', Timestamptz: 'timestamptz', Timestamp: 'timestamp', Date: 'date' };

function sqlType(type, attrs) {
  const unsupported = type.match(/^Unsupported\("(.+)"\)$/);
  if (unsupported) return unsupported[1];
  const db = attrs.match(/@db\.(\w+)(?:\(([^)]*)\))?/);
  if (db) {
    const [, kind, args] = db;
    if (kind === 'VarChar') return `varchar(${args})`;
    if (kind === 'Char') return `char(${args})`;
    if (kind === 'Decimal') return `decimal(${args.replace(/\s/g, '')})`;
    const base = DB[kind] ?? kind.toLowerCase();
    return args ? `${base}(${args})` : base;
  }
  if (enums.has(type)) return type;
  return BASE[type] ?? type;
}

const tables = [];
const byModel = new Map();
for (const [name, lines] of models) {
  const table = { model: name, name: lines.find((l) => l.startsWith('@@map'))?.match(/"(.+)"/)[1] ?? name, columns: [], refs: [], uniques: [], pk: [] };
  const compositeId = lines.find((l) => l.startsWith('@@id'));
  for (const line of lines) {
    if (line.startsWith('@@')) {
      const u = line.match(/^@@unique\(\[([^\]]+)\]/);
      if (u) table.uniques.push(u[1].split(',').map((s) => s.trim()));
      continue;
    }
    const m = line.match(/^(\w+)\s+([\w]+(?:\("[^"]*"\))?)(\[\])?(\?)?\s*(.*)$/);
    if (!m) continue;
    const [, field, type, list, optional, attrs] = m;
    if (models.has(type)) {
      const rel = attrs.match(/@relation\([^)]*fields:\s*\[([^\]]+)\][^)]*references:\s*\[([^\]]+)\]/);
      if (rel) table.refs.push({ fields: rel[1].split(',').map((s) => s.trim()), target: type, targetFields: rel[2].split(',').map((s) => s.trim()), optional: Boolean(optional) });
      continue;
    }
    table.columns.push({
      field,
      name: attrs.match(/@map\("([^"]+)"\)/)?.[1] ?? field,
      type: sqlType(type, attrs) + (list ? '[]' : ''),
      optional: Boolean(optional),
      pk: /@id\b/.test(attrs),
      unique: /@unique\b/.test(attrs),
      isEnum: enums.has(type),
    });
  }
  if (compositeId) table.pk = compositeId.match(/\[([^\]]+)\]/)[1].split(',').map((s) => s.trim());
  else table.pk = table.columns.filter((c) => c.pk).map((c) => c.field);
  tables.push(table);
  byModel.set(name, table);
}

const col = (t, field) => t.columns.find((c) => c.field === field);
const fkFields = (t) => new Set(t.refs.flatMap((r) => r.fields));
const isOneToOne = (t, ref) => ref.fields.length === 1 && (col(t, ref.fields[0])?.unique || (t.pk.length === 1 && t.pk[0] === ref.fields[0]));

// PlantUML (IE notation)
const head = (title) => `@startuml\n!include _style.iuml\ntitle ${title}\nhide circle\nhide empty members\nskinparam linetype ortho\nskinparam class {\n  AttributeFontSize 10\n}\n`;
const relLines = () => {
  const out = [];
  for (const t of tables) {
    for (const r of t.refs) {
      const target = byModel.get(r.target);
      const parentEnd = r.optional ? '|o' : '||';
      const childEnd = isOneToOne(t, r) ? 'o|' : 'o{';
      out.push(`${target.name} ${parentEnd}--${childEnd} ${t.name}`);
    }
  }
  return out.join('\n');
};

function entity(t, columns) {
  const fks = fkFields(t);
  const rows = columns.map((c) => {
    const key = t.pk.includes(c.field) ? '<<PK>> ' : '';
    const fk = fks.has(c.field) ? ' <<FK>>' : '';
    const star = c.optional ? '' : '* ';
    return `  ${star}${key}${c.name} : ${c.type}${fk}`;
  });
  const pkRows = rows.filter((_, i) => t.pk.includes(columns[i].field));
  const rest = rows.filter((_, i) => !t.pk.includes(columns[i].field));
  return `entity "${t.name}" as ${t.name} {\n${pkRows.join('\n')}\n  --\n${rest.join('\n')}\n}\n`;
}

let physical = head('VRMS physical schema (PostgreSQL 16, database vrms)');
for (const t of tables) physical += entity(t, t.columns);
physical += `${relLines()}\n@enduml\n`;
writeFileSync(path.join(here, '4.5.2-physical-schema.puml'), physical.replace('@startuml', '@startuml 4.5.2-physical-schema'));

// Logical ERD: business tables only, keys plus up to 4 main attributes, without audit stamps.
// The sync, settings and permission copy tables appear only in the physical schema (4.5.2).
const NOT_BUSINESS = new Set(['vrms_people', 'role_permissions', 'permission_matrix', 'permission_sync_state', 'directory_sync_state', 'app_settings', 'settings_state', 'setting_changes']);
const META = /^(created|updated|edited|deleted|purged|actor|.*ByUserId$|.*ByName$|.*ByEmail$|leaseOwner|leaseUntil|failingSince)/;
let logical = head('VRMS entity relationship diagram');
for (const t of tables) {
  if (NOT_BUSINESS.has(t.name)) continue;
  const fks = fkFields(t);
  const keep = t.columns.filter((c) => t.pk.includes(c.field) || fks.has(c.field));
  const main = t.columns.filter((c) => !keep.includes(c) && !META.test(c.field)).slice(0, 4);
  logical += entity(t, [...keep, ...main]);
}
logical += `${relLines()}\n@enduml\n`;
writeFileSync(path.join(here, '4.5.1-erd.puml'), logical.replace('@startuml', '@startuml 4.5.1-erd'));

console.log(`${tables.length} tables, ${enums.size} enums, ${tables.reduce((n, t) => n + t.refs.length, 0)} relations`);
