import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'03_Backend'))
from app.configuration import validate_configuration

class ConfigurationValidation(unittest.TestCase):
    def indicator(self):return {'id':'review_count','name':'Cases awaiting review','type':'KRI','metric':'review_count','direction':'lower','visible':True,'warning':5,'critical':10}
    def test_valid_kri(self):validate_configuration('acquisition',{'settings':{'slaDays':5},'indicators':[self.indicator()]})
    def test_duplicate_id(self):
        with self.assertRaises(ValueError):validate_configuration('acquisition',{'indicators':[self.indicator(),self.indicator()]})
    def test_no_executable_formulas(self):
        item=self.indicator();item['metric']='eval(1)'
        with self.assertRaises(ValueError):validate_configuration('acquisition',{'indicators':[item]})
    def test_invalid_threshold_direction(self):
        item=self.indicator();item['critical']=1
        with self.assertRaises(ValueError):validate_configuration('acquisition',{'indicators':[item]})
    def test_invalid_scenario(self):
        for value in (-1,91,float('nan')):
            with self.assertRaises(ValueError):validate_configuration('risk',{'settings':{'cashShock':value}})
    def test_nonempty_memo_template(self):
        with self.assertRaises(ValueError):validate_configuration('memo',{'settings':{'chapters':[]}})
        validate_configuration('memo',{'settings':{'chapters':['Summary','Evidence and outstanding actions']}})
    def test_finite_targets(self):
        item=self.indicator();item['target']=float('inf')
        with self.assertRaises(ValueError):validate_configuration('risk',{'indicators':[item]})
    def test_scope_and_units(self):
        with self.assertRaises(ValueError):validate_configuration('unknown',{})
        with self.assertRaises(ValueError):validate_configuration('financials',{'settings':{'units':'invented_fx'}})

if __name__=='__main__':unittest.main(verbosity=2)
