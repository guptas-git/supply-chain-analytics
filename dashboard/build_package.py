"""Rebuild the Tableau extracts and portable workbook from ETL exports.

Run from any directory after installing dashboard/requirements.txt.
"""
import csv
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from tableauhyperapi import (Connection, CreateMode, HyperProcess, SqlType,
                             TableDefinition, TableName, Telemetry, escape_string_literal)

ROOT = Path(__file__).resolve().parent
ET.register_namespace('user', 'http://www.tableausoftware.com/xml/user')
TYPES = {'string': SqlType.text, 'date': SqlType.date,
         'integer': SqlType.big_int, 'real': SqlType.double}


def main():
    tree = ET.parse(ROOT / 'Supply_Chain_Performance.twb')
    workbook = tree.getroot()
    extracts = ROOT / 'Data'
    extracts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='olist-tableau-') as temp:
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
            for source in workbook.findall('./datasources/datasource'):
                relation = source.find('./connection/relation')
                name = relation.get('name').removesuffix('.csv')
                path = ROOT.parent / 'exports' / (name + '.csv')
                with path.open(newline='', encoding='utf-8') as stream:
                    reader = csv.reader(stream)
                    header = next(reader)
                    expected_rows = sum(1 for _ in reader)
                columns = relation.findall('./columns/column')
                if header != [c.get('name') for c in columns]:
                    raise ValueError(f'{name}: CSV columns differ from workbook schema')
                table = TableDefinition(TableName('Extract', 'Extract'), [
                    TableDefinition.Column(c.get('name'), TYPES[c.get('datatype')]()) for c in columns
                ])
                staged = Path(temp) / (name + '.hyper')
                with Connection(hyper.endpoint, staged, CreateMode.CREATE_AND_REPLACE) as conn:
                    conn.catalog.create_schema('Extract')
                    conn.catalog.create_table(table)
                    rows = conn.execute_command(
                        f"COPY {table.table_name} FROM {escape_string_literal(str(path))} "
                        "WITH (format => 'csv', header => true)"
                    )
                    if rows != expected_rows or rows == 0:
                        raise ValueError(f'{name}: expected {expected_rows} rows, loaded {rows}')
                    if name == 'order_facts':
                        unique = conn.execute_scalar_query('SELECT count(DISTINCT order_id) FROM "Extract"."Extract"')
                        if unique != rows:
                            raise ValueError('order_facts: duplicate or missing order IDs')
                staged.replace(extracts / staged.name)
                print(f'{name}: {rows:,} rows')

    for conn in workbook.findall('.//connection[@class="hyper"]'):
        conn.set('dbname', 'Data/' + Path(conn.get('dbname')).name)
    for conn in workbook.findall('.//connection[@class="textscan"]'):
        conn.set('directory', 'Data')
    package = ROOT / 'Supply_Chain_Performance.twbx'
    with tempfile.TemporaryDirectory(prefix='olist-package-') as temp:
        staged = Path(temp) / package.name
        with ZipFile(staged, 'w', ZIP_DEFLATED) as archive:
            archive.writestr('Supply_Chain_Performance.twb', ET.tostring(workbook, encoding='utf-8', xml_declaration=True))
            for name in ['order_facts', 'seller_performance']:
                archive.write(extracts / (name + '.hyper'), 'Data/' + name + '.hyper')
                archive.write(ROOT.parent / 'exports' / (name + '.csv'), 'Data/' + name + '.csv')
        with ZipFile(staged) as archive:
            if archive.testzip() is not None:
                raise ValueError('Package checksum validation failed')
        staged.replace(package)
    print(f'Built {package.name}')


if __name__ == '__main__':
    main()
