import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import urllib.error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'core'))
import cli
import evidence
from http_cache import CachedFetcher

FEED=b'<rss><channel><item><guid>1</guid><title>News</title><link>https://example.org/story</link></item></channel></rss>'
SOURCE={'id':'news','kind':'rss','url':'https://example.org/rss'}

class NewsroomTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'config').mkdir();(self.root/'config/profile.json').write_text('{}')
        self.db=evidence.connect(self.root)
        evidence.collect(self.db,[SOURCE],lambda _:FEED)
    def tearDown(self):self.db.close();self.tmp.cleanup()
    def call(self,action,**kw):return cli.run(self.root,'newsroom',dict(action=action,**kw))
    def assess(self,run_id):
        batch=self.call('batch',run_id=run_id)
        return self.call('assess',run_id=run_id,items=[dict(item_id=i['item_id'],relevance='irrelevant',reason='No change to goals',asset_or_goal_refs=[]) for i in batch['items']])
    def test_restart_coverage_and_receipt_gate(self):
        r=self.call('start');key=r['id']
        self.assertEqual(self.call('start')['id'],key)
        with self.assertRaises(ValueError):self.call('finish',run_id=key,reason='premature')
        self.assertEqual(self.assess(key)['pending'],0)
        self.call('finish',run_id=key,report='Synthetic test report',reason='Checked',material_key='synthetic-claim')
        with self.assertRaises(ValueError):self.call('receipt',run_id=key,channel='matrix',status='delivered',reference='fake')
        self.call('dispatch',run_id=key)
        self.assertEqual(self.call('start')['state'],'delivery_pending')
        with self.assertRaises(ValueError):self.call('dispatch',run_id=key)
        self.call('receipt',run_id=key,channel='audio',status='skipped',reference='absent')
        self.assertEqual(self.call('status',run_id=key)['state'],'delivery_pending')
        self.assertEqual(self.call('receipt',run_id=key,channel='matrix',status='delivered',reference='test-event-id')['state'],'delivered')
        fresh=self.call('start')
        self.assertEqual(fresh['total'],0)
        with self.assertRaises(ValueError):self.call('finish',run_id=fresh['id'],report='Different wording',reason='checked',material_key='synthetic-claim')
    def test_profile_change_reopens_archive(self):
        r=self.call('start');self.assess(r['id']);self.call('finish',run_id=r['id'],reason='Nothing new')
        (self.root/'config/profile.json').write_text('{"goals":["new goal"]}')
        r=self.call('start');self.assertTrue(r['profile_changed']);self.assertEqual(r['pending'],1)
    def test_atomic_assessments(self):
        r=self.call('start');i=self.call('batch',run_id=r['id'])['items'][0]
        with self.assertRaises(ValueError):self.call('assess',run_id=r['id'],items=[dict(item_id=i['item_id'],relevance='relevant',reason='yes',asset_or_goal_refs=[] )])
        self.assertEqual(self.call('status',run_id=r['id'])['pending'],1)
    def test_cached_304_and_backoff(self):
        class Opener:
            def open(inner,req,timeout):
                if req.get_header('If-none-match')=='v1':raise urllib.error.HTTPError(req.full_url,304,'Not modified',{},None)
                response=io.BytesIO(FEED);response.url=req.full_url;response.headers={'ETag':'v1'};return response
        cache=CachedFetcher(self.db,Opener());cache.save([SOURCE],evidence.collect(self.db,[SOURCE],cache))
        cache=CachedFetcher(self.db,Opener());r=cache.save([SOURCE],evidence.collect(self.db,[SOURCE],cache))
        self.assertEqual(r['sources'][0]['fetch_state'],'not_modified');self.assertFalse(r['degraded'])
        class RateLimit:
            def open(inner,req,timeout):raise urllib.error.HTTPError(req.full_url,429,'rate limit',{'Retry-After':'3600'},None)
        cache=CachedFetcher(self.db,RateLimit());r=cache.save([SOURCE],evidence.collect(self.db,[SOURCE],cache));self.assertTrue(r['degraded'])
        cache=CachedFetcher(self.db,RateLimit());r=cache.save([SOURCE],evidence.collect(self.db,[SOURCE],cache));self.assertEqual(r['sources'][0]['fetch_state'],'deferred')
    def test_bad_xml_does_not_commit_validator(self):
        class Opener:
            def open(inner,req,timeout):
                response=io.BytesIO(b'bad xml');response.url=req.full_url;response.headers={'ETag':'bad'};return response
        cache=CachedFetcher(self.db,Opener());r=cache.save([SOURCE],evidence.collect(self.db,[SOURCE],cache))
        self.assertTrue(r['degraded']);self.assertEqual(self.db.execute('SELECT COUNT(*) FROM http_cache').fetchone()[0],0)
