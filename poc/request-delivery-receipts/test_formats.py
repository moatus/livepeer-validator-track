"""Signed malformed-profile regressions. Private keys never serialized."""
import copy,hashlib,json,pathlib,unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from verifier import verify
ROOT=pathlib.Path(__file__).parent
OBSERVATIONS=[]
def signing_bytes(payload):
    body=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
    return b''.join(len(p).to_bytes(8,'big')+p for p in (b'receipt005-v1',b'receipt',body))
class Formats(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate();self.trust=json.loads((ROOT/'trust.json').read_text());self.trust['public_key_hex']=self.key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
    def check(self,name,body,fmt,accepted=False):
        e=json.loads((ROOT/'fixtures/honest_json/receipt.json').read_text());c=json.loads((ROOT/'fixtures/honest_json/customer.json').read_text());c['delivered_response_hex']=body.hex()
        assets={}
        if fmt=='media':
            asset=b'actual independent asset bytes';assets={'mock://asset/one':hashlib.sha256(asset).hexdigest()};c['delivered_assets']={'mock://asset/one':asset.hex()}
        e['payload'].update(format=fmt,response_sha256=hashlib.sha256(body).hexdigest(),assets=assets)
        e['signature']=self.key.sign(signing_bytes(e['payload'])).hex()
        result=verify(e,c,self.trust,set());OBSERVATIONS.append(dict(case=name,format=fmt,body_hex=body.hex(),matching_delivery_hash=True,signature_verified_independently=True,expected_acceptance=accepted,result=result))
        self.key.public_key().verify(bytes.fromhex(e['signature']),signing_bytes(e['payload']))
        self.assertEqual(result['scope']=='exchange_verified',accepted,name)
        if not accepted:self.assertEqual(result['reason'],'MALFORMED_EVIDENCE',name)
    def test_signed_encoding_regressions(self):
        self.check('review_a_utf16_sse',b'data: '+ '{"x":1}'.encode('utf-16')+b'\n\ndata: [DONE]\n\n','sse')
        for enc in ['utf-16','utf-32']:
            self.check(enc+'_json','{"x":1}'.encode(enc),'json')
            self.check(enc+'_media','{"asset_url":"mock://asset/one"}'.encode(enc),'media')
    def test_signed_nonfinite_regressions(self):
        for constant in ['NaN','Infinity','-Infinity']:
            body=('{"x":'+constant+'}').encode()
            self.check(constant+'_json',body,'json')
            self.check(constant+'_sse',b'data: '+body+b'\n\ndata: [DONE]\n\n','sse')
            # Single valid media key: nonfinite value forces strict parser rejection,
            # independently of later record shape/type or asset checks.
            self.check(constant+'_media',('{"asset_url":'+constant+'}').encode(),'media')
    def test_nonascii_utf8_controls(self):
        self.check('valid_nonascii_json','{"réponse":"蓝色圆圈"}'.encode(),'json',True)
        self.check('valid_nonascii_sse',b'data: '+'{"delta":"蓝色圆圈"}'.encode()+b'\n\ndata: [DONE]\n\n','sse',True)
        # URI may contain UTF-8; media lookup must still use exact decoded URI.
        e=json.loads((ROOT/'fixtures/honest_media/receipt.json').read_text());c=json.loads((ROOT/'fixtures/honest_media/customer.json').read_text());uri='mock://asset/蓝色';asset=bytes.fromhex(next(iter(c['delivered_assets'].values())))
        body=json.dumps({'asset_url':uri},ensure_ascii=False,separators=(',',':')).encode();c['delivered_response_hex']=body.hex();c['delivered_assets']={uri:asset.hex()};e['payload'].update(response_sha256=hashlib.sha256(body).hexdigest(),assets={uri:hashlib.sha256(asset).hexdigest()});e['signature']=self.key.sign(signing_bytes(e['payload'])).hex()
        result=verify(e,c,self.trust,set());self.key.public_key().verify(bytes.fromhex(e['signature']),signing_bytes(e['payload']))
        OBSERVATIONS.append(dict(case='valid_nonascii_media',format='media',body_hex=body.hex(),matching_delivery_hash=True,signature_verified_independently=True,expected_acceptance=True,result=result));self.assertEqual(result['scope'],'exchange_verified')
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Formats);result=unittest.TextTestRunner(verbosity=2).run(suite)
    out=dict(total_signed_cases=len(OBSERVATIONS),invalid_rejected=sum(not r['expected_acceptance'] and r['result']['scope']!='exchange_verified' for r in OBSERVATIONS),valid_accepted=sum(r['expected_acceptance'] and r['result']['scope']=='exchange_verified' for r in OBSERVATIONS),failures=len(result.failures)+len(result.errors),observations=OBSERVATIONS)
    (ROOT/'format-regressions.json').write_text(json.dumps(out,indent=2)+'\n');raise SystemExit(not result.wasSuccessful())
