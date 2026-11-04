"""Run regression cases and write auditable latency/error metrics."""
import argparse, asyncio, json, statistics, time
from datetime import datetime, timezone
from pathlib import Path
import httpx

async def run_one(client, base_url, item):
    started=time.perf_counter(); result=None; answer=None; error=None; stages=[]; status=None
    try:
        async with client.stream('POST', f'{base_url}/api/query', json={'query':item['question']}) as response:
            status=response.status_code; response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith('data: '): continue
                payload=json.loads(line[6:].strip())
                if 'stage' in payload: stages.append(payload['stage'])
                if 'result' in payload: result=payload['result']
                if 'answer' in payload: answer=payload['answer']
                if 'error' in payload: error=str(payload['error'])
    except Exception as exc: error=f'{type(exc).__name__}: {exc}'
    latency=round((time.perf_counter()-started)*1000,2)
    keys=sorted(result[0].keys()) if isinstance(result,list) and result else []
    expected=item.get('expected','').split(',') if item.get('expected') else []
    if item['type'] in {'chitchat','capability'}: ok=bool(answer) and not error
    elif item['type']=='unknown_metric': ok=bool(error or answer) and not (result and expected and set(expected)<=set(keys))
    else: ok=bool(result) and set(expected)<=set(keys) and not error
    return {'id':item['id'],'type':item['type'],'ok':ok,'status':status,'latency_ms':latency,'stages':stages,'keys':keys,'error':error}

async def main(base_url, limit, output):
    items=json.loads(Path(__file__).with_name('questions.json').read_text()); items=items[:limit] if limit else items
    async with httpx.AsyncClient(timeout=180) as client: results=[await run_one(client,base_url,i) for i in items]
    latencies=[r['latency_ms'] for r in results]; passed=sum(r['ok'] for r in results)
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'base_url':base_url,'cases':len(results),'passed':passed,'pass_rate':round(passed/len(results),4) if results else 0,'latency_ms':{'p50':round(statistics.median(latencies),2) if latencies else None,'p95':round(sorted(latencies)[max(0,int(len(latencies)*.95)-1)],2) if latencies else None,'max':max(latencies) if latencies else None},'results':results}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,ensure_ascii=False,indent=2)); print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if passed==len(results) else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--base-url',default='http://127.0.0.1:8000'); p.add_argument('--limit',type=int); p.add_argument('--output',type=Path,default=Path('evals/reports/latest.json')); a=p.parse_args(); raise SystemExit(asyncio.run(main(a.base_url,a.limit,a.output)))
