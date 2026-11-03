"""Consequential boundary mutations, using ephemeral synthetic signer only."""
import copy,json,pathlib,unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from verifier import verify,framed,canonical,sha
ROOT=pathlib.Path(__file__).parent
class Boundaries(unittest.TestCase):
    def setUp(self):
        self.trust=json.loads((ROOT/'trust.json').read_text());self.e=json.loads((ROOT/'fixtures/honest_json/receipt.json').read_text());self.c=json.loads((ROOT/'fixtures/honest_json/customer.json').read_text())
    def test_delivery_and_missing_observer(self):
        self.c['delivered_response_hex']=b'{}\n'.hex();self.assertEqual(verify(self.e,self.c,self.trust,set())['reason'],'DELIVERY_MISMATCH')
        del self.c['delivered_response_hex'];self.assertEqual(verify(self.e,self.c,self.trust,set())['scope'],'unverified')
    def test_replay_state(self):
        state=set();self.assertEqual(verify(self.e,self.c,self.trust,state)['scope'],'exchange_verified');self.assertEqual(verify(self.e,self.c,self.trust,state)['reason'],'JOB_ALREADY_CONSUMED')
    def test_freshness_and_forged_metadata(self):
        del self.c['fresh_challenge_issued'];self.assertEqual(verify(self.e,self.c,self.trust,set())['reason'],'NO_INDEPENDENT_FRESHNESS')
        self.e['payload']['canonical_model']='fake';self.assertEqual(verify(self.e,self.c,self.trust,set())['reason'],'SIGNATURE_INVALID')
    def test_attacker_key_never_becomes_trust(self):
        key=Ed25519PrivateKey.generate();self.e['public_key_hex']=key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex();self.e['signature']=key.sign(framed('receipt',canonical(self.e['payload']))).hex()
        self.assertEqual(verify(self.e,self.c,self.trust,set())['reason'],'SIGNATURE_INVALID')
    def test_valid_signature_cannot_make_truncated_sse_complete(self):
        key=Ed25519PrivateKey.generate();self.trust['public_key_hex']=key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
        body=b'data: {"delta":"prefix"}\n\n';self.c['delivered_response_hex']=body.hex();self.e['payload']['format']='sse';self.e['payload']['response_sha256']=sha(body);self.e['signature']=key.sign(framed('receipt',canonical(self.e['payload']))).hex()
        self.assertEqual(verify(self.e,self.c,self.trust,set())['reason'],'SSE_INCOMPLETE')
    def test_media_byte_lookup(self):
        self.e=json.loads((ROOT/'fixtures/honest_media/receipt.json').read_text());self.c=json.loads((ROOT/'fixtures/honest_media/customer.json').read_text())
        self.c['delivered_assets']['mock://asset/one']=b'wrong asset'.hex();self.assertEqual(verify(self.e,self.c,self.trust,set())['reason'],'ASSET_MISMATCH')
        del self.c['delivered_assets'];self.assertEqual(verify(self.e,self.c,self.trust,set())['scope'],'unverified')
    def test_sse_order_bytes_matter(self):
        self.e=json.loads((ROOT/'fixtures/honest_sse/receipt.json').read_text());self.c=json.loads((ROOT/'fixtures/honest_sse/customer.json').read_text())
        events=bytes.fromhex(self.c['delivered_response_hex']).split(b'\n\n');events[0],events[1]=events[1],events[0];self.c['delivered_response_hex']=b'\n\n'.join(events).hex()
        self.assertEqual(verify(self.e,self.c,self.trust,set())['reason'],'DELIVERY_MISMATCH')
if __name__=='__main__': unittest.main()
