import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'core'))
import evidence
import cli

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'config').mkdir()
        (self.root/'config/profile.json').write_text('{"assets": []}')
        (self.root/'config/sources.json').write_text('{"sources": []}')
    def tearDown(self):
        self.temp.cleanup()
    def test_collection_revision_provenance(self):
        source = {'id':'news','kind':'rss','url':'https://example.org/rss','role':'news_discovery'}
        feed = b'<rss><channel><item><guid>1</guid><title>New possibility</title><link>https://example.org/story</link><description>Evidence</description></item></channel></rss>'
        db = evidence.connect(self.root)
        try:
            self.assertEqual(evidence.collect(db,[source],lambda _:feed)['sources'][0]['added'],1)
            self.assertEqual(evidence.collect(db,[source],lambda _:feed)['sources'][0]['added'],0)
            self.assertEqual(evidence.collect(db,[source],lambda _:feed.replace(b'Evidence',b'Revised'))['sources'][0]['added'],1)
            self.assertEqual(evidence.bundle(db,{},2)['items'][0]['provenance']['role'],'news_discovery')
        finally: db.close()
    def test_dossier_roundtrip_and_prepare(self):
        doc = {'id':'q1','question':'Can existing hardware do this?','goal':'Less manual effort','constraints':[], 'unknowns':['Latency'], 'next_searches':['runtime latency benchmarks'], 'decision':'investigate', 'evidence':[{'claim':'A runtime changed','source':'https://example.org/release','observed_at':'2026-01-01','basis':'external-claim'}]}
        cli.run(self.root,'dossier',{'action':'upsert','document':doc})
        bundle = cli.run(self.root,'prepare',{})
        self.assertEqual(bundle['dossiers'][0],doc)
        self.assertIn('host agent',bundle['research_contract']['mode'])
        self.assertEqual(cli.run(self.root,'status',{})['dossier_count'],1)
    def test_reject_unsubstantiated_proposal(self):
        with self.assertRaises(ValueError):
            cli.validate_dossier({'id':'q','question':'Q','goal':'G','constraints':[],'unknowns':[],'next_searches':[],'decision':'propose','evidence':[]})
    def test_reject_runtime_inside_code(self):
        with self.assertRaises(ValueError): cli.run(Path(__file__).resolve().parents[1]/'runtime','status',{})
    def test_reject_bad_limit(self):
        with self.assertRaises(ValueError): cli.run(self.root,'prepare',{'limit':True})
    def test_feed_failures_are_visible(self):
        db=evidence.connect(self.root)
        try:
            result=evidence.collect(db,[{'id':'bad','kind':'rss','url':'https://example.org/rss'}],lambda _:b'not XML')
            self.assertIsNotNone(result['sources'][0]['error'])
            self.assertEqual(evidence.status(db)['items'],0)
        finally: db.close()
