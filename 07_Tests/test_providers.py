import asyncio
import pytest
from app.providers import validate_file,interpret

def test_file_type_spoofing():
    with pytest.raises(ValueError):validate_file('statement.pdf',b'<html>not a pdf</html>')
    with pytest.raises(ValueError):validate_file('script.exe',b'data')
    with pytest.raises(ValueError):validate_file('image.png',b'bad')

def test_no_fabrication_without_cloud_credentials():
    result=asyncio.run(interpret([{'page':1,'text':'Revenue 2000000 / إيرادات'}]))
    assert result['fields']==[]
    assert 'not configured' in result['warning']
