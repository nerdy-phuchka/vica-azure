from app.transactions import parse_schedule,summarise

def test_arabic_schedule_not_auto_classified():
    text='التاريخ,الوصف,مدين,دائن,الرصيد\n2025-01-01,تحصيل عميل,٠,٥٠٠٠٠,٥٠٠٠٠\n'
    rows=parse_schedule('arabic.csv',text.encode())
    assert rows[0]['credit']=='50000'
    assert not rows[0]['reviewed']
    assert summarise(rows)['unreviewed_count']==1
    rows[0].update(reviewed=True,category='operating_receipt')
    assert summarise(rows)['reviewed_net_by_category']['operating_receipt']=='50000.0000'
