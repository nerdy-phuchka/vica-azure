import json
from pathlib import Path
from .finance import number


def load_policy(synthetic=False):
    from .config import settings
    path = Path(settings().policy_file)
    if synthetic:
        path = path.with_name('policy.demo.json')
    policy = json.loads(path.read_text(encoding='utf-8'))
    if policy.get('status') not in ('pending_confirmation','demo','approved'):
        raise ValueError('Unsupported policy approval state')
    if policy.get('status')=='approved':
        if not policy.get('approved_by') or not policy.get('source') or not policy.get('version'):
            raise ValueError('Approved policy requires approval evidence, source and version')
        if not policy.get('rules') or any(r.get('status')!='active' or not r.get('source_page') for r in policy['rules']):
            raise ValueError('Approved policy requires active, source-referenced rules')
    if policy.get('status') == 'demo' and not synthetic:
        raise ValueError('Demonstration policy cannot assess real cases')
    return policy


def evaluate(policy, metrics):
    results = []
    operators = {'gt':lambda a,b:a>b, 'gte':lambda a,b:a>=b,
                 'lt':lambda a,b:a<b, 'lte':lambda a,b:a<=b, 'eq':lambda a,b:a==b}
    for rule in policy['rules']:
        result = {'rule_id':rule['id'], 'description':rule['description'],
                  'source':policy['source'], 'source_page':rule.get('source_page'),
                  'hard_stop':rule.get('hard_stop',False)}
        if rule.get('status') != 'active':
            result['outcome'] = 'pending_confirmation'
        else:
            actual = number(metrics.get(rule['field']))
            result.update(actual=None if actual is None else str(actual), threshold=rule['value'])
            if actual is None:
                result['outcome'] = 'missing_input'
            elif rule.get('operator') not in operators:
                raise ValueError('Unsupported policy operator')
            else:
                result['outcome'] = 'pass' if operators[rule['operator']](actual,number(rule['value'])) else 'fail'
        results.append(result)
    return results
