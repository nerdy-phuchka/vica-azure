from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

TRANSLATE = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')


def number(value):
    if value is None or str(value).strip() == '':
        return None
    text = str(value).translate(TRANSLATE).replace('٬','').replace('٫','.').replace(',','').replace(' ','')
    if text.startswith('(') and text.endswith(')'):
        text = '-'+text[1:-1]
    try:
        result = Decimal(text)
        if not result.is_finite() or abs(result) > Decimal('1e18'):
            raise ValueError('Numeric value outside supported bounds')
        return result
    except InvalidOperation:
        raise ValueError('Invalid numeric value; supply currency and units separately')


def fmt(value):
    return None if value is None else str(value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))


def amortisation(principal,annual_rate,months):
    """Illustrative level monthly payments. No fees, grace period or balloon; not an Islamic product contract."""
    amount=number(principal);rate=number(annual_rate)
    if amount is None or rate is None or amount<=0 or rate<0 or rate>100 or not 1<=months<=120:
        raise ValueError('Invalid repayment schedule inputs')
    cent=Decimal('0.01')
    with localcontext() as context:
        context.prec=38
        monthly=rate/Decimal('1200')
        payment=amount/months if monthly==0 else amount*monthly/(1-(1+monthly)**(-months))
        payment=payment.quantize(cent,rounding=ROUND_HALF_UP)
        balance=amount;rows=[]
        for month in range(1,months+1):
            interest=(balance*monthly).quantize(cent,rounding=ROUND_HALF_UP)
            principal_part=min(balance,payment-interest) if month<months else balance
            actual_payment=principal_part+interest
            balance-=principal_part
            rows.append({'month':month,'payment':str(actual_payment),'interest':str(interest),
                         'principal':str(principal_part),'closing_balance':str(balance.quantize(cent))})
        return {'rows':rows,'first_year_debt_service':str(sum(number(row['payment']) for row in rows[:12])),
                'assumption':'Illustrative level monthly amortisation; no fees, grace periods or balloon. Confirm product terms.'}


def calculate(values):
    """All values are reviewed base-currency figures for one explicitly selected period."""
    def v(key):
        return number(values.get(key))
    def ratio(a, b, scale=1):
        return None if a is None or b is None or b <= 0 else a/b*scale
    revenue, debt, equity = v('revenue'), v('total_debt'), v('equity')
    cash, existing, proposed = v('cash_available'), v('existing_debt_service'), v('proposed_debt_service')
    service = None if existing is None or proposed is None else existing+proposed
    current, inventory, liabilities = v('current_assets'), v('inventory'), v('current_liabilities')
    prior = v('prior_revenue')
    metrics = {
      'revenue':revenue,
      'revenue_growth_pct':ratio(None if revenue is None or prior is None else revenue-prior, prior, 100),
      'gross_margin_pct':ratio(v('gross_profit'), revenue, 100),
      'net_margin_pct':ratio(v('net_profit'), revenue, 100),
      'current_ratio':ratio(current, liabilities),
      'quick_ratio':ratio(None if current is None or inventory is None else current-inventory, liabilities),
      'debt_to_equity':ratio(debt, equity),
      'liabilities_to_equity':ratio(v('total_liabilities'), equity),
      'interest_coverage':ratio(v('ebit'), v('interest_expense')),
      'inventory_turnover':ratio(v('cost_of_sales'), v('average_inventory')),
      'collection_days':ratio(v('average_receivables'), v('credit_sales'), 365),
      'dscr':ratio(cash, service),
      'downside_dscr':ratio(None if cash is None else cash*Decimal('0.8'), service),
      'debt_service':service
    }
    return {'metrics':{k:fmt(val) for k,val in metrics.items()},
            'assumptions':['Cash available must be reviewed annual cash available for debt service, not EBITDA.',
                           'Existing and proposed debt service must cover the same annual period.',
                           'Downside scenario reduces cash available by 20%; this is a prototype assumption, not a policy threshold.',
                           'All reviewed figures must be base currency and a consistent assessment period.',
                           'Non-positive ratio denominators produce unavailable results, not zero.'],
            'warnings':[f'{key}: unavailable or invalid denominator/input' for key,val in metrics.items() if val is None]}
