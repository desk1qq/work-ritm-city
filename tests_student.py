import json,unittest,urllib.request,urllib.error,os
BUILD=os.environ.get('BUILD','A')
def request(method,path,body=None,version=None,key=None):
 h={'Content-Type':'application/json','X-Build':BUILD}
 if version is not None:h['If-Match']=str(version)
 if key is not None:h['Idempotency-Key']=key
 r=urllib.request.Request('http://127.0.0.1:8766'+path,data=None if body is None else json.dumps(body).encode(),headers=h,method=method)
 try:response=urllib.request.urlopen(r,timeout=3)
 except urllib.error.HTTPError as e:response=e
 with response:return response.status,json.load(response)

class ContractTests(unittest.TestCase):
 def setUp(self):request('POST','/api/reset',{})
 
 def test_initial_fixture(self):
  status,rows=request('GET','/api/shows')
  self.assertEqual(status,200)
  self.assertEqual(len(rows),3)
  self.assertEqual(request('GET','/api/shows/101')[1]['version'],1)
  
 def test_unknown(self):
  self.assertEqual(request('GET','/api/shows/999'),(404,{'code':'NOT_FOUND'}))

 def test_idempotency_repeat(self):
  status, body = request("PATCH", "/api/shows/101", {"start": 1090}, version=1, key="k1")
  self.assertEqual(status, 200)
  self.assertEqual(body["version"], 2)
  status, body2 = request("PATCH", "/api/shows/101", {"start": 1090}, version=1, key="k1")
  self.assertEqual(status, 200)
  self.assertEqual(body2["version"], 2)
  status, audit = request("GET", "/api/audit")
  self.assertEqual(len(audit), 1)

 def test_state_after_failure(self):
  status, rows_before = request("GET", "/api/shows")
  status, audit_before = request("GET", "/api/audit")
  status, body = request("PATCH", "/api/shows/101", {"start": 1120}, version=1, key="k2")
  self.assertEqual(status, 409)
  status, rows_after = request("GET", "/api/shows")
  status, audit_after = request("GET", "/api/audit")
  self.assertEqual(rows_before, rows_after)
  self.assertEqual(audit_before, audit_after)
  status, body = request("PATCH", "/api/shows/101", {"start": 1060}, version=1, key="k2")
  self.assertEqual(status, 200)

 def test_stale_version(self):
  request("PATCH", "/api/shows/101", {"status": "published"}, version=1, key="k3a")
  status, body = request("PATCH", "/api/shows/101", {"duration": 50}, version=1, key="k3b")
  self.assertEqual(status, 412)

 def test_interval_touch(self):
  status, body = request("PATCH", "/api/shows/101", {"start": 1090, "duration": 40}, version=1, key="k4")
  self.assertEqual(status, 200)

if __name__=='__main__':unittest.main(verbosity=2)