"""Conditional HTTP fetches and durable deferred retry, never blocking retry loops."""
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
import evidence


class CachedFetcher:
    def __init__(self, db, opener=None):
        db.execute('''CREATE TABLE IF NOT EXISTS http_cache(
          url TEXT PRIMARY KEY, etag TEXT, modified TEXT, next_attempt REAL NOT NULL DEFAULT 0,
          failures INTEGER NOT NULL DEFAULT 0)''')
        db.commit()
        self.db=db
        self.previous={r['url']:dict(r) for r in db.execute('SELECT * FROM http_cache')}
        self.updates={}
        self.states={}
        self.opener=opener or urllib.request.build_opener(evidence.PublicRedirect())
        self.host_locks={}
        self.lock=threading.Lock()

    def __call__(self,url):
        evidence.public_url(url)
        prior=self.previous.get(url,{})
        if prior.get('next_attempt',0)>time.time():
            self.states[url]='deferred'
            return None
        headers={'User-Agent':'HomeRadar/0.2-alpha','Accept':'application/json, application/atom+xml, application/rss+xml, application/xml, text/xml'}
        if prior.get('etag'):headers['If-None-Match']=prior['etag']
        if prior.get('modified'):headers['If-Modified-Since']=prior['modified']
        host=urllib.parse.urlsplit(url).netloc
        with self.lock: host_lock=self.host_locks.setdefault(host,threading.Lock())
        try:
            with host_lock, self.opener.open(urllib.request.Request(url,headers=headers),timeout=evidence.TIMEOUT) as response:
                evidence.public_url(response.url)
                body=response.read(evidence.MAX_BYTES+1)
                if len(body)>evidence.MAX_BYTES:raise ValueError('Source too large')
                self.updates[url]=(response.headers.get('ETag'),response.headers.get('Last-Modified'),0,0)
                self.states[url]='fetched'
                return body
        except urllib.error.HTTPError as error:
            if error.code==304:
                error.close()
                if not prior.get('etag') and not prior.get('modified'):raise ValueError('Unexpected 304 without cached evidence')
                self.states[url]='not_modified'
                self.updates[url]=(prior.get('etag'),prior.get('modified'),0,0)
                return None
            failures=prior.get('failures',0)+1
            delay=min(86400,60*2**min(failures,10))
            retry=error.headers.get('Retry-After')
            if retry:
                try:delay=max(delay,int(retry))
                except ValueError:
                    try:delay=max(delay,parsedate_to_datetime(retry).timestamp()-time.time())
                    except (ValueError,TypeError,OverflowError):pass
            if error.headers.get('X-RateLimit-Remaining')=='0':
                try:delay=max(delay,float(error.headers.get('X-RateLimit-Reset'))-time.time())
                except (TypeError,ValueError):pass
            self.updates[url]=(prior.get('etag'),prior.get('modified'),time.time()+delay,failures)
            self.states[url]='failed'
            raise
        except Exception:
            failures=prior.get('failures',0)+1
            self.updates[url]=(prior.get('etag'),prior.get('modified'),time.time()+min(86400,60*2**min(failures,10)),failures)
            self.states[url]='failed'
            raise

    def save(self, sources, results):
        # Persist validators only after successful parsing + evidence transaction.
        by_id={s['id']:s for s in sources}
        with self.db:
            for result in results['sources']:
                url=by_id[result['source_id']]['url']
                state=self.states.get(url)
                result['fetch_state']=state
                update=self.updates.get(url)
                if update and (not result['error'] or state=='failed'):
                    self.db.execute('INSERT OR REPLACE INTO http_cache VALUES (?,?,?,?,?)',(url,*update))
        results['degraded']=any(r['error'] or r.get('fetch_state')=='deferred' for r in results['sources'])
        return results
