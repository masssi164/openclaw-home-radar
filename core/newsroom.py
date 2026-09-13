"""Durable, restart-safe editorial accounting. No model or delivery side effects."""
import hashlib
import json
import uuid
import evidence


def setup(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS triage(item_id TEXT PRIMARY KEY, assessed_at TEXT, payload TEXT);
    CREATE TABLE IF NOT EXISTS radar_runs(
      id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      state TEXT NOT NULL, profile_hash TEXT NOT NULL, report TEXT, report_hash TEXT,
      material_key TEXT, outcome_reason TEXT);
    CREATE UNIQUE INDEX IF NOT EXISTS radar_one_active ON radar_runs((1))
      WHERE state IN ('researching','ready','delivery_pending');
    CREATE TABLE IF NOT EXISTS radar_run_items(
      run_id TEXT NOT NULL REFERENCES radar_runs(id), item_id TEXT NOT NULL REFERENCES items(item_id),
      assessment TEXT, PRIMARY KEY(run_id,item_id));
    CREATE TABLE IF NOT EXISTS radar_receipts(
      run_id TEXT NOT NULL REFERENCES radar_runs(id), channel TEXT NOT NULL,
      status TEXT NOT NULL, reference TEXT NOT NULL, observed_at TEXT NOT NULL,
      PRIMARY KEY(run_id,channel));
    ''')


def text(value):
    return isinstance(value, str) and bool(value.strip())


def summary(db, run_id):
    row=db.execute('SELECT * FROM radar_runs WHERE id=?',(run_id,)).fetchone()
    if row is None: raise ValueError('Unknown run')
    result=dict(row)
    counts=db.execute('SELECT COUNT(*),COUNT(assessment) FROM radar_run_items WHERE run_id=?',(run_id,)).fetchone()
    result.update(total=counts[0], assessed=counts[1], pending=counts[0]-counts[1])
    result['receipts']=[dict(r) for r in db.execute('SELECT * FROM radar_receipts WHERE run_id=?',(run_id,))]
    return result


def run(db, profile, payload):
    setup(db)
    action=payload.get('action','status')
    if action=='start':
        # Serialize snapshot + active-run creation, including concurrent invocations.
        with db:
            db.execute('BEGIN IMMEDIATE')
            active=db.execute("SELECT id FROM radar_runs WHERE state IN ('researching','ready','delivery_pending')").fetchone()
            if active: return dict(summary(db,active['id']),resumed=True)
            run_id=uuid.uuid4().hex
            stamp=evidence.now()
            digest=hashlib.sha256(evidence.canonical(profile).encode()).hexdigest()
            previous=db.execute('SELECT profile_hash FROM radar_runs ORDER BY created_at DESC LIMIT 1').fetchone()
            # Changed profile reopens archived evidence; reasoning still belongs to the host.
            recheck=previous is not None and previous[0]!=digest
            db.execute('INSERT INTO radar_runs(id,created_at,updated_at,state,profile_hash) VALUES (?,?,?,?,?)',
                       (run_id,stamp,stamp,'researching',digest))
            query='SELECT item_id FROM items' if recheck else 'SELECT item_id FROM items WHERE item_id NOT IN (SELECT item_id FROM triage)'
            db.execute('INSERT INTO radar_run_items(run_id,item_id) SELECT ?,item_id FROM ('+query+')',(run_id,))
        return dict(summary(db,run_id),resumed=False,profile_changed=recheck)
    if action=='list':
        return {'runs':[summary(db,r[0]) for r in db.execute('SELECT id FROM radar_runs ORDER BY created_at DESC LIMIT 10')]}
    run_id=payload.get('run_id')
    current=summary(db,run_id)
    if action=='status': return current
    if action=='batch':
        limit=payload.get('limit',25)
        if type(limit) is not int or not 1<=limit<=50:raise ValueError('limit must be 1..50')
        return {'run_id':run_id,'pending':current['pending'],'items':[evidence.bounded_item(r) for r in db.execute('''
          SELECT i.* FROM radar_run_items r JOIN items i USING(item_id)
          WHERE r.run_id=? AND r.assessment IS NULL ORDER BY i.source_id,i.published_at DESC,i.item_id LIMIT ?''',(run_id,limit))]}
    if action=='assess':
        if current['state']!='researching':raise ValueError('Run is not researching')
        rows=payload.get('items')
        if not isinstance(rows,list) or not 1<=len(rows)<=50:raise ValueError('Expected 1..50 assessments')
        seen=set()
        for r in rows:
            if not isinstance(r,dict) or not text(r.get('item_id')):raise ValueError('Expected assessment')
            key=r['item_id']
            if key in seen or not db.execute('SELECT 1 FROM radar_run_items WHERE run_id=? AND item_id=?',(run_id,key)).fetchone():raise ValueError('Unexpected or duplicate item')
            seen.add(key)
            if r.get('relevance') not in ('relevant','irrelevant','needs_context') or not text(r.get('reason')):raise ValueError('Semantic decision and reason required')
            refs=r.get('asset_or_goal_refs')
            if not isinstance(refs,list) or not all(text(x) for x in refs) or (r['relevance']=='relevant' and not refs):raise ValueError('Context references required')
        with db:
            for r in rows:
                body=evidence.canonical(r)
                db.execute('UPDATE radar_run_items SET assessment=? WHERE run_id=? AND item_id=?',(body,run_id,r['item_id']))
                db.execute('INSERT OR REPLACE INTO triage VALUES (?,?,?)',(r['item_id'],evidence.now(),body))
            db.execute('UPDATE radar_runs SET updated_at=? WHERE id=?',(evidence.now(),run_id))
        return summary(db,run_id)
    if action=='finish':
        if current['state']!='researching' or current['pending']:raise ValueError('Complete triage before finishing')
        reason=payload.get('reason')
        if not text(reason):raise ValueError('Editorial outcome reason required')
        report=payload.get('report','')
        if not isinstance(report,str) or len(report)>60000:raise ValueError('Invalid report')
        key=payload.get('material_key')
        if report.strip() and not text(key):raise ValueError('Material claims key required')
        if report.strip() and db.execute("SELECT 1 FROM radar_runs WHERE material_key=? AND state IN ('delivered','delivery_pending')",(key,)).fetchone():raise ValueError('Already delivered or uncertain material claims; reconcile first')
        state='ready' if report.strip() else 'no_findings'
        with db:
            db.execute('UPDATE radar_runs SET state=?,report=?,report_hash=?,material_key=?,outcome_reason=?,updated_at=? WHERE id=?',
                       (state,report,hashlib.sha256(report.encode()).hexdigest(),key,reason,evidence.now(),run_id))
        return summary(db,run_id)
    if action=='dispatch':
        if current['state']!='ready':raise ValueError('Report not ready; uncertain delivery must be reconciled')
        # Record before host I/O. A restart cannot silently retry an uncertain send.
        with db:db.execute("UPDATE radar_runs SET state='delivery_pending',updated_at=? WHERE id=?",(evidence.now(),run_id))
        return summary(db,run_id)
    if action=='receipt':
        channel=payload.get('channel'); status=payload.get('status'); reference=payload.get('reference')
        if channel not in ('matrix','audio') or status not in ('delivered','failed','unknown','skipped'):raise ValueError('Invalid receipt')
        if current['state'] not in ('delivery_pending','delivered'):raise ValueError('No dispatched report')
        if not text(reference):raise ValueError('Actual receipt or diagnostic reference required')
        with db:
            db.execute('INSERT OR REPLACE INTO radar_receipts VALUES (?,?,?,?,?)',(run_id,channel,status,reference,evidence.now()))
            if channel=='matrix':
                state='delivered' if status=='delivered' else ('ready' if status=='failed' else 'delivery_pending')
                db.execute('UPDATE radar_runs SET state=?,updated_at=? WHERE id=?',(state,evidence.now(),run_id))
        return summary(db,run_id)
    raise ValueError('Unknown newsroom action')
