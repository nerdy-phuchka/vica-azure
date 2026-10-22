from typing import Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ApplicationIn(BaseModel):
    borrower_name: str = Field(min_length=2, max_length=200)
    requested_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: Literal['SAR','AED','USD'] = 'SAR'
    product: Literal['working_capital','term_loan','lease'] = 'working_capital'
    purpose: str = Field(default='', max_length=2000)
    tenor_months: int = Field(default=12,ge=1,le=120)
    proposed_annual_rate: Decimal | None = Field(default=None,ge=0,le=100,max_digits=8,decimal_places=4)
    borrower_contribution: Decimal = Field(default=Decimal('0'),ge=0,max_digits=18,decimal_places=2)
    security_details: str = Field(default='',max_length=4000)
    los_reference: str = Field(default='', max_length=100)
    synthetic: bool = False
    members: list[str] = Field(default_factory=list, max_length=30)


FIELDS = {
 'legal_name','registration_number','incorporation_date','licence_expiry',
 'authorised_signatory','beneficial_owners','revenue','prior_revenue','gross_profit',
 'net_profit','current_assets','inventory','current_liabilities','total_debt',
 'total_liabilities','equity','ebit','interest_expense','cost_of_sales',
 'average_inventory','average_receivables','credit_sales','cash_available',
 'existing_debt_service','proposed_debt_service','operating_receipts',
 'operating_payments','loan_proceeds','owner_injections','internal_transfers',
 'tax_paid','capital_expenditure','reporting_period','audit_opinion','currency','unit_multiplier'
}
NUMERIC = FIELDS - {'legal_name','registration_number','incorporation_date','licence_expiry',
 'authorised_signatory','beneficial_owners','reporting_period','audit_opinion','currency'}


class FieldIn(BaseModel):
    name: str
    value: str = Field(max_length=3000)
    document_id: str | None = None
    page: int | None = Field(default=None, ge=1)
    quote: str = Field(default='', max_length=4000)
    rationale: str = Field(min_length=3, max_length=2000)
    @field_validator('name')
    @classmethod
    def allowed(cls, value):
        if value not in FIELDS:
            raise ValueError('Unsupported field')
        return value


class ReviewField(BaseModel):
    value: str = Field(max_length=3000)
    rationale: str = Field(min_length=3, max_length=2000)
    expected_version: int


class NoteIn(BaseModel):
    text: str = Field(min_length=3, max_length=6000)
    category: Literal['comment','field_visit','legal','compliance','fraud'] = 'comment'


class ClearanceIn(BaseModel):
    category: Literal['legal','compliance','fraud','field_visit']
    status: Literal['clear','hold','not_applicable']
    rationale: str = Field(min_length=10, max_length=4000)
    document_ids: list[str] = Field(default_factory=list)
    expected_version: int


class TransitionIn(BaseModel):
    action: Literal['submit','review_accept','return']
    expected_version: int
    rationale: str = Field(min_length=3, max_length=2000)


class DecisionIn(BaseModel):
    decision: Literal['approved','conditional','declined','deferred']
    expected_version: int
    rationale: str = Field(min_length=10, max_length=4000)
    conditions: list[str] = Field(default_factory=list, max_length=30)


class ConditionIn(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    evidence: str = Field(min_length=3, max_length=4000)


class QuestionIn(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class MemberIn(BaseModel):
    subject: str = Field(min_length=3, max_length=100)
    expected_version: int
