from decimal import Decimal
import pytest
from app.finance import number,calculate

def test_arabic_digits_and_negative():
    assert number('١٬٢٣٤٫٥٠')==Decimal('1234.50')
    assert number('(250)')==Decimal('-250')
    assert number('') is None

@pytest.mark.parametrize('value',['NaN','Infinity','SAR 12','1e100'])
def test_invalid_numbers(value):
    with pytest.raises(ValueError):number(value)

def test_debt_service_not_ebitda():
    result=calculate({'cash_available':'300000','existing_debt_service':'100000',
      'proposed_debt_service':'100000','revenue':'2000000','prior_revenue':'1600000'})
    assert result['metrics']['dscr']=='1.5000'
    assert result['metrics']['downside_dscr']=='1.2000'
    assert result['metrics']['revenue_growth_pct']=='25.0000'
    assert calculate({'ebit':'900000'})['metrics']['dscr'] is None

def test_non_positive_denominator_and_missing_not_zero():
    assert calculate({'equity':'0','total_debt':'100'})['metrics']['debt_to_equity'] is None
    assert calculate({'equity':'-20','total_debt':'100'})['metrics']['debt_to_equity'] is None
    assert calculate({})['metrics']['revenue'] is None
