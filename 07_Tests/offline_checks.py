"""Dependency-free checks runnable before external package installation. Not a substitute for pytest."""
import ast
import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import unittest
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'03_Backend'))
spec=importlib.util.spec_from_file_location('finance',root/'03_Backend/app/finance.py')
finance=importlib.util.module_from_spec(spec);spec.loader.exec_module(finance)

class OfflineChecks(unittest.TestCase):
    def test_python_sources_parse(self):
        files=list(root.rglob('*.py'))
        self.assertGreater(len(files),15)
        for path in files:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    def test_json_parses(self):
        for path in root.rglob('*.json'):json.loads(path.read_text(encoding='utf-8'))
    def test_arabic_numbers(self):
        self.assertEqual(finance.number('١٬٢٣٤٫٥٠'),Decimal('1234.50'))
    def test_missing_zero_and_negative(self):
        self.assertIsNone(finance.number(''))
        self.assertIsNone(finance.calculate({'equity':'-1','total_debt':'2'})['metrics']['debt_to_equity'])
        self.assertIsNone(finance.calculate({'cash_available':'200','existing_debt_service':'0'})['metrics']['dscr'])
    def test_repayment_calculation(self):
        result=finance.calculate({'cash_available':'300000','existing_debt_service':'100000','proposed_debt_service':'100000'})
        self.assertEqual(result['metrics']['dscr'],'1.5000')
        self.assertEqual(result['metrics']['downside_dscr'],'1.2000')
    def test_invalid_numeric(self):
        for value in ['NaN','Infinity','SAR 1','1e100']:
            with self.assertRaises(ValueError):finance.number(value)
    def test_schedule_principal_conservation(self):
        for rate in ('0','8.5'):
            result=finance.amortisation('250000',rate,24)
            self.assertEqual(sum(Decimal(r['principal']) for r in result['rows']),Decimal('250000'))
            self.assertEqual(Decimal(result['rows'][-1]['closing_balance']),Decimal('0'))
    def test_policy_separation(self):
        pending=json.loads((root/'02_Configuration/policy.pending.json').read_text(encoding='utf-8'))
        demo=json.loads((root/'02_Configuration/policy.demo.json').read_text(encoding='utf-8'))
        self.assertEqual(len(pending['rules']),10)
        self.assertTrue(all(r['status']=='pending' for r in pending['rules']))
        self.assertEqual(demo['status'],'demo')
    def test_actual_policy_evaluator(self):
        from app.policy import evaluate
        policy=json.loads((root/'02_Configuration/policy.demo.json').read_text())
        self.assertEqual([r['outcome'] for r in evaluate(policy,{'revenue':'2000000','dscr':'1.5'})],['pass','pass'])
        self.assertEqual(evaluate(policy,{'revenue':'0','dscr':None})[1]['outcome'],'missing_input')
        self.assertEqual(evaluate(policy,{'revenue':'0','dscr':'0'})[0]['outcome'],'fail')
    def test_actual_arabic_statement_parser(self):
        from app.transactions import parse_schedule,summarise
        data=(root/'08_Sample_Data/04_arabic_statement.csv').read_bytes()
        tx=parse_schedule('arabic.csv',data)
        self.assertEqual(len(tx),3)
        self.assertEqual(summarise(tx)['unreviewed_count'],3)
        self.assertEqual(tx[0]['credit'],'50000')

if __name__=='__main__':unittest.main(verbosity=2)
