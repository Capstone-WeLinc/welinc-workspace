#!/usr/bin/env node
// Gateway checks for spec 0008, AC-1 to AC-21. Run from the workspace root (Node 24 and Docker):
//   node infra/gateway/test/check-routes.mjs          start the harness, check, remove it
//   node infra/gateway/test/check-routes.mjs --keep   leave the harness running afterwards
// Exits non zero when any check fails.
import { spawnSync } from 'node:child_process';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomBytes } from 'node:crypto';

const here = path.dirname(fileURLToPath(import.meta.url));
const composeFile = path.join(here, 'compose.yml');
const IMAGE = 'welinc-gateway-test:local';
const GW = 3100; // TRUST_EDGE_PROXY=0, no HSTS, a high flood limit
const EDGE = 3101; // TRUST_EDGE_PROXY=1, HSTS max-age=60, 5 a second with a burst of 5
const LISTED = 'http://localhost:8001';
const UNLISTED = 'http://evil.example';
const STUBS = ['auth-service', 'vrms-backend', 'vmms-backend', 'vmms-analytics', 'bms-gateway'];
const MB = 1024 * 1024;
const keep = process.argv.includes('--keep');

// ---------- helpers ----------

const run = (cmd, args) => spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 64 * MB });
const compose = (...args) => run('docker', ['compose', '-f', composeFile, ...args]);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const marker = () => `m${randomBytes(6).toString('hex')}`;

const results = [];
function check(ac, name, ok, detail = '') {
  results.push({ ac, name, ok });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${ac.padEnd(6)} ${name}${!ok && detail ? `\n        ${detail}` : ''}`);
}

/** One HTTP request. Resolves { status, headers, raw, body, json } or { error } on a socket error. */
function request(port, { method = 'GET', url = '/', headers = {}, body } = {}) {
  return new Promise((resolve) => {
    const req = http.request(
      { host: '127.0.0.1', port, method, path: url, headers, agent: false },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          let json;
          try {
            json = JSON.parse(text);
          } catch {
            json = undefined;
          }
          resolve({ status: res.statusCode, headers: res.headers, raw: res.rawHeaders, body: text, json });
        });
        res.on('error', (error) => resolve({ error: error.code ?? String(error) }));
      },
    );
    req.on('error', (error) => resolve({ error: error.code ?? String(error) }));
    if (body !== undefined) req.end(body);
    else req.end();
  });
}

/** Every value of one header in the raw response (rawHeaders keeps repeats apart). */
function headerValues(res, name) {
  const out = [];
  for (let i = 0; i < (res.raw ?? []).length; i += 2) {
    if (res.raw[i].toLowerCase() === name.toLowerCase()) out.push(res.raw[i + 1]);
  }
  return out;
}
const corsHeaderNames = (res) =>
  (res.raw ?? []).filter((_, i) => i % 2 === 0).filter((h) => h.toLowerCase().startsWith('access-control-'));

const isGatewayError = (res, status, code) =>
  res.status === status &&
  /^application\/json/.test(res.headers?.['content-type'] ?? '') &&
  res.json?.statusCode === status &&
  res.json?.code === code &&
  typeof res.json?.message === 'string' &&
  typeof res.json?.error === 'string';

const hasErrorHeaders = (res, origin = LISTED) =>
  res.headers?.['access-control-allow-origin'] === origin &&
  res.headers?.['access-control-allow-credentials'] === 'true' &&
  /Origin/.test(res.headers?.vary ?? '') &&
  /^[A-Za-z0-9._-]{1,64}$/.test(res.headers?.['x-request-id'] ?? '');

const brief = (res) =>
  res.error ? `socket error ${res.error}` : `status ${res.status}, body ${res.body?.slice(0, 160)}`;

const logsOf = (service) => compose('logs', '--no-log-prefix', service).stdout ?? '';

async function waitFor(fn, timeoutMs) {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    if (await fn()) return true;
    await sleep(300);
  }
  return false;
}

// ---------- start ----------

console.log('Starting the gateway harness (first run builds the image)...');
compose('down', '-v', '--remove-orphans');
const up = compose('up', '-d', '--build');
if (up.status !== 0) {
  console.error(up.stderr);
  process.exit(1);
}

try {
  const ready = await waitFor(async () => {
    // The edge gateway allows 5 a second, so it gets one probe a round
    const probes = await Promise.all([
      ...['/auth/', '/vrms/', '/vmms/', '/vmms/analytics/', '/bms/'].map((p) => request(GW, { url: `${p}ready` })),
      request(EDGE, { url: '/vrms/ready' }),
    ]);
    return probes.every((r) => r.status === 200);
  }, 60_000);
  if (!ready) throw new Error('The harness did not come up within 60 seconds');

  // The 30 s route is timed out live; start it now and collect it at the end
  const timeoutCheck = request(GW, { url: '/auth/slow?delay=31000', headers: { Origin: LISTED } });

  // ---------- AC-1, AC-2, AC-17: routing ----------
  const routes = [
    ['/auth/login?a=1&b=two', 'auth', 'auth-service:3001'],
    ['/uploads/avatars/x.png', 'auth', 'auth-service:3001'],
    ['/vrms/repairs/a%2Fb?q=%20x&q=2', 'vrms', 'vrms-backend:3002'],
    ['/vmms/analytics/forecast?days=7', 'vmms-analytics', 'vmms-analytics:3011'],
    ['/vmms/vehicles/1', 'vmms', 'vmms-backend:3010'],
    ['/vmms/analyticsx', 'vmms', 'vmms-backend:3010'],
    ['/bms/bookings?page=2', 'bms', 'bms-gateway:3020'],
  ];
  for (const [url, service, host] of routes) {
    const res = await request(GW, { url });
    const ac = url.startsWith('/vmms') ? 'AC-2' : 'AC-1';
    check(ac, `${url} reaches ${service} with the path and query unchanged`,
      res.status === 200 && res.json?.service === service && res.json?.url === url, brief(res));
    check('AC-17', `${url} sends Host ${host}`, res.json?.headers?.host === host, `host ${res.json?.headers?.host}`);
  }

  // ---------- AC-3: outside the table ----------
  const m3 = marker();
  for (const p of ['/', '/repairs/x', '/vmmsx', '/auth', '/uploads', '/vrms', '/vmms', '/vmms/analytics', '/bms', '/nope.png']) {
    const res = await request(GW, { url: `${p}?m=${m3}`, headers: { Origin: LISTED } });
    check('AC-3', `${p} answers the JSON 404`, isGatewayError(res, 404, 'NOT_FOUND'), brief(res));
    if (p === '/nope.png') check('AC-11', '404 carries CORS and X-Request-Id', hasErrorHeaders(res), JSON.stringify(res.headers));
  }
  check('AC-3', 'none of those reached an upstream', STUBS.every((s) => !logsOf(s).includes(m3)));

  // ---------- AC-8, AC-10: CORS on a proxied answer ----------
  {
    const res = await request(GW, { url: '/vrms/x?cors=1', headers: { Origin: LISTED } });
    const acao = headerValues(res, 'access-control-allow-origin');
    check('AC-8', 'a listed origin gets its exact origin, credentials and Vary: Origin',
      acao.length === 1 && acao[0] === LISTED && res.headers['access-control-allow-credentials'] === 'true' &&
        headerValues(res, 'vary').join(',') === 'Origin', JSON.stringify(res.headers));
    check('AC-10', "the upstream's own CORS, Vary, X-Request-Id and HSTS never reach the browser",
      !headerValues(res, 'access-control-allow-methods').length && !headerValues(res, 'access-control-max-age').length &&
        headerValues(res, 'access-control-expose-headers').join() === 'X-Request-Id, Retry-After' &&
        headerValues(res, 'x-request-id').length === 1 && res.headers['x-request-id'] !== 'from-upstream' &&
        !headerValues(res, 'strict-transport-security').length, JSON.stringify(res.raw));
    const bad = await request(GW, { url: '/vrms/x?cors=1', headers: { Origin: UNLISTED } });
    check('AC-8', 'an unlisted origin gets no Access-Control-* header', bad.status === 200 && corsHeaderNames(bad).length === 0,
      corsHeaderNames(bad).join());
    const none = await request(GW, { url: '/vrms/x' });
    check('AC-8', 'no origin at all gets no Access-Control-* header, and nothing answers *',
      corsHeaderNames(none).length === 0 && !JSON.stringify(res.raw).includes('"*"'));
  }

  // ---------- AC-9: preflight ----------
  {
    const m9 = marker();
    const pre = { 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type' };
    const res = await request(GW, { method: 'OPTIONS', url: `/vrms/x?m=${m9}`, headers: { Origin: LISTED, ...pre } });
    check('AC-9', 'a listed preflight answers 204 with methods, headers and max age',
      res.status === 204 && res.headers['access-control-allow-origin'] === LISTED &&
        res.headers['access-control-allow-credentials'] === 'true' &&
        res.headers['access-control-allow-methods'] === 'GET, POST, PUT, PATCH, DELETE, OPTIONS' &&
        res.headers['access-control-allow-headers'] === 'Authorization, Content-Type, X-Request-Id' &&
        res.headers['access-control-max-age'] === '600', JSON.stringify(res.headers));
    const bad = await request(GW, { method: 'OPTIONS', url: `/vrms/x?m=${m9}`, headers: { Origin: UNLISTED, ...pre } });
    check('AC-9', 'an unlisted preflight answers 204 with no Access-Control-* header', bad.status === 204 && corsHeaderNames(bad).length === 0,
      `${bad.status} ${corsHeaderNames(bad).join()}`);
    check('AC-9', 'preflights reach no upstream', !logsOf('vrms-backend').includes(m9));
  }

  // ---------- AC-11: upstream errors pass through ----------
  for (const status of [503, 502]) {
    const res = await request(GW, { url: `/vrms/health?status=${status}` });
    check('AC-11', `an upstream ${status} passes through with its own body`, res.status === status && res.json?.service === 'vrms', brief(res));
  }

  // ---------- AC-12: session refresh for VMMS and BMS ----------
  for (const [url, origin] of [['/vmms/session/refresh', 'http://localhost:8002'], ['/bms/session/refresh', 'http://localhost:8003']]) {
    const pre = await request(GW, { method: 'OPTIONS', url, headers: { Origin: origin, 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type' } });
    const res = await request(GW, { method: 'POST', url, headers: { Origin: origin, 'Content-Type': 'application/json', Cookie: 'stub_rt=0' }, body: '{}' });
    check('AC-12', `${url} from ${origin} passes CORS with credentials and Set-Cookie intact`,
      pre.status === 204 && pre.headers['access-control-allow-origin'] === origin &&
        res.status === 200 && res.headers['access-control-allow-origin'] === origin &&
        res.headers['access-control-allow-credentials'] === 'true' &&
        headerValues(res, 'set-cookie').join() === 'stub_rt=1; Path=/; HttpOnly', JSON.stringify(res.headers));
  }

  // ---------- AC-15, AC-18: forwarded headers and request id on the plain gateway ----------
  {
    const plain = await request(GW, { url: '/vrms/x' });
    const planted = await request(GW, { url: '/vrms/x', headers: { 'X-Forwarded-For': '6.6.6.6, 7.7.7.7', 'X-Forwarded-Proto': 'https' } });
    const xff = plain.json?.headers?.['x-forwarded-for'];
    check('AC-15', 'X-Forwarded-For is one value, the same whether or not the caller sent one',
      typeof xff === 'string' && !xff.includes(',') && planted.json?.headers?.['x-forwarded-for'] === xff,
      `${xff} vs ${planted.json?.headers?.['x-forwarded-for']}`);
    check('AC-15', "X-Forwarded-Proto is the gateway's own scheme", planted.json?.headers?.['x-forwarded-proto'] === 'http',
      planted.json?.headers?.['x-forwarded-proto']);

    const kept = await request(GW, { url: '/vrms/x', headers: { 'X-Request-Id': 'abc.DEF_1-2' } });
    check('AC-18', 'a valid caller id is kept upstream and in the response',
      kept.json?.headers?.['x-request-id'] === 'abc.DEF_1-2' && kept.headers['x-request-id'] === 'abc.DEF_1-2');
    for (const badId of ['bad id!', 'x'.repeat(65), undefined]) {
      const res = await request(GW, { url: '/vrms/x', headers: badId === undefined ? {} : { 'X-Request-Id': badId } });
      const sent = res.json?.headers?.['x-request-id'];
      check('AC-18', `${badId === undefined ? 'no id' : `id "${badId.slice(0, 12)}"`} is replaced by a generated one`,
        /^[0-9a-f]{32}$/.test(sent ?? '') && res.headers['x-request-id'] === sent, `${sent} / ${res.headers['x-request-id']}`);
    }
    const pre = await request(GW, { method: 'OPTIONS', url: '/vrms/x', headers: { Origin: LISTED, 'X-Request-Id': 'pre-1' } });
    const health = await request(GW, { url: '/health', headers: { 'X-Request-Id': 'health-1' } });
    const notFound = await request(GW, { url: '/nowhere', headers: { 'X-Request-Id': 'nf-1' } });
    check('AC-18', 'preflight, /health and errors carry the id',
      pre.headers['x-request-id'] === 'pre-1' && health.headers['x-request-id'] === 'health-1' && notFound.headers['x-request-id'] === 'nf-1');
  }

  // ---------- AC-21: HSTS ----------
  {
    const answers = async (port) => [
      await request(port, { url: '/vrms/x?cors=1' }),
      await request(port, { method: 'OPTIONS', url: '/vrms/x', headers: { Origin: LISTED } }),
      await request(port, { url: '/nowhere' }),
      await request(port, { url: '/health' }),
    ];
    const off = await answers(GW);
    check('AC-21', 'with GATEWAY_HSTS empty, no answer carries HSTS', off.every((r) => !headerValues(r, 'strict-transport-security').length));
    const on = await answers(EDGE);
    check('AC-21', 'with GATEWAY_HSTS set, proxied, preflight, error and /health answers carry it',
      on.every((r) => headerValues(r, 'strict-transport-security').join() === 'max-age=60'),
      on.map((r) => headerValues(r, 'strict-transport-security').join('|')).join(' / '));
  }

  // ---------- AC-16: behind an edge proxy ----------
  {
    const res = await request(EDGE, { url: '/vrms/x', headers: { 'X-Forwarded-For': '9.9.9.9, 5.6.7.8', 'X-Forwarded-Proto': 'https' } });
    check('AC-16', 'X-Forwarded-For is the last incoming entry', res.json?.headers?.['x-forwarded-for'] === '5.6.7.8', res.json?.headers?.['x-forwarded-for']);
    check('AC-16', 'X-Forwarded-Proto is the incoming https', res.json?.headers?.['x-forwarded-proto'] === 'https');
    const odd = await request(EDGE, { url: '/vrms/x', headers: { 'X-Forwarded-For': '5.6.7.9', 'X-Forwarded-Proto': 'gopher' } });
    check('AC-16', 'an incoming proto other than http or https is replaced', odd.json?.headers?.['x-forwarded-proto'] === 'http');
  }

  // ---------- AC-19: flood limit ----------
  {
    await sleep(1500); // let the edge's bucket drain after the checks above
    const flood = await Promise.all(
      Array.from({ length: 30 }, () => request(EDGE, { url: '/vrms/x', headers: { 'X-Forwarded-For': '10.0.0.1', Origin: LISTED } })),
    );
    const limited = flood.filter((r) => r.status === 429);
    check('AC-19', 'past the limit a caller gets the JSON 429 with Retry-After: 1',
      limited.length > 0 && limited.every((r) => isGatewayError(r, 429, 'RATE_LIMITED') && r.headers['retry-after'] === '1'),
      `${limited.length} of 30 limited; ${limited[0] ? brief(limited[0]) : ''}`);
    if (limited[0]) check('AC-11', '429 carries CORS and X-Request-Id', hasErrorHeaders(limited[0]));
    const other = await request(EDGE, { url: '/vrms/x', headers: { 'X-Forwarded-For': '10.0.0.2' } });
    check('AC-19', "one client's flood doesn't limit another address", other.status === 200, brief(other));
    const preflights = await Promise.all(
      Array.from({ length: 30 }, () => request(EDGE, { method: 'OPTIONS', url: '/vrms/x', headers: { 'X-Forwarded-For': '10.0.0.1', Origin: LISTED } })),
    );
    const healths = await Promise.all(Array.from({ length: 30 }, () => request(EDGE, { url: '/health', headers: { 'X-Forwarded-For': '10.0.0.1' } })));
    check('AC-19', 'preflights and GET /health are never counted',
      preflights.every((r) => r.status === 204) && healths.every((r) => r.status === 200));
  }

  // ---------- AC-6: body limits ----------
  for (const [prefix, limitMb] of [['/auth/', 5], ['/uploads/', 5], ['/vrms/', 26], ['/vmms/analytics/', 1], ['/vmms/', 10], ['/bms/', 10]]) {
    const limit = limitMb * MB;
    const at = await request(GW, { method: 'POST', url: `${prefix}upload`, headers: { 'Content-Type': 'application/octet-stream', Origin: LISTED }, body: Buffer.alloc(limit) });
    const over = await request(GW, { method: 'POST', url: `${prefix}upload`, headers: { 'Content-Type': 'application/octet-stream', Origin: LISTED }, body: Buffer.alloc(limit + 1) });
    check('AC-6', `${prefix} takes exactly ${limitMb} MB and refuses one byte more`,
      at.status === 200 && at.json?.bytes === limit && (over.error !== undefined || isGatewayError(over, 413, 'PAYLOAD_TOO_LARGE')),
      `at: ${brief(at).slice(0, 80)}; over: ${brief(over)}`);
    if (over.status === 413) check('AC-11', `${prefix} 413 carries CORS and X-Request-Id`, hasErrorHeaders(over));
  }

  // ---------- AC-5, AC-11, AC-20: a stopped system ----------
  {
    compose('stop', 'bms-gateway');
    // For up to 5 s (the resolver's valid=5s) nginx still holds the old address and its connect
    // times out (504). After that the name no longer resolves: the steady 502 this checks.
    await sleep(6000);
    const secrets = { Origin: LISTED, Authorization: 'Bearer secrettoken', Cookie: 'sid=secretcookie' };
    const down = await request(GW, { url: '/bms/session/callback?code=topsecret', headers: secrets });
    check('AC-5', 'a stopped system answers the JSON 502 on its routes', isGatewayError(down, 502, 'UPSTREAM_UNAVAILABLE'), brief(down));
    check('AC-11', '502 carries CORS and X-Request-Id', hasErrorHeaders(down), JSON.stringify(down.headers));
    const others = await Promise.all(['/auth/x', '/vrms/x', '/vmms/x', '/vmms/analytics/x'].map((url) => request(GW, { url })));
    check('AC-5', 'every other route keeps working', others.every((r) => r.status === 200));
    compose('start', 'bms-gateway');
    const started = Date.now();
    const back = await waitFor(async () => (await request(GW, { url: '/bms/x' })).status === 200, 10_000);
    check('AC-5', 'the system works again within 10 seconds, no gateway restart', back, `${Date.now() - started} ms`);

    await request(GW, { url: '/vrms/x?code=topsecret2', headers: secrets });
    await sleep(500);
    const log = logsOf('gateway');
    check('AC-20', 'query strings, Authorization and Cookie never reach the container log',
      !/topsecret|secrettoken|secretcookie/.test(log));
    const line = log.split('\n').map((l) => { try { return JSON.parse(l); } catch { return undefined; } }).find((l) => l?.request_id === 'abc.DEF_1-2');
    const fields = ['time', 'request_id', 'client', 'method', 'path', 'status', 'bytes', 'duration', 'upstream', 'upstream_status', 'upstream_duration'];
    check('AC-20', 'each proxied request logs one JSON line with every field',
      !!line && fields.every((f) => f in line) && line.path === '/vrms/x' && line.status === 200, JSON.stringify(line));
    check('AC-18', 'the access log shows the same request id', !!line);
    check('AC-20', 'GET /health is not logged', !log.includes('health-1'));
  }

  // ---------- AC-7: timeouts ----------
  {
    const res = await timeoutCheck;
    check('AC-7', 'an upstream past the 30 s read timeout answers the JSON 504', isGatewayError(res, 504, 'UPSTREAM_TIMEOUT'), brief(res));
    if (res.status === 504) check('AC-11', '504 carries CORS and X-Request-Id', hasErrorHeaders(res));
    const dump = compose('exec', '-T', 'gateway', 'nginx', '-T').stdout ?? '';
    const loaded = {};
    for (const [, loc, block] of dump.matchAll(/location (\S+) \{([^}]*)\}/g)) {
      loaded[loc] = [block.match(/client_max_body_size (\S+);/)?.[1], block.match(/proxy_read_timeout (\S+);/)?.[1]];
    }
    const table = { '/auth/': ['5m', '30s'], '/uploads/': ['5m', '30s'], '/vrms/': ['26m', '120s'], '/vmms/analytics/': ['1m', '120s'], '/vmms/': ['10m', '60s'], '/bms/': ['10m', '60s'] };
    for (const [loc, want] of Object.entries(table)) {
      check('AC-7', `${loc} loads ${want[0]} and ${want[1]}`, loaded[loc]?.join() === want.join(), `loaded ${loaded[loc]}`);
    }
    check('AC-7', 'every route connects within 5 s', /proxy_connect_timeout 5s;/.test(dump));
  }

  // ---------- AC-13: settings checks ----------
  {
    const base = {
      AUTH_UPSTREAM: 'http://auth-service:3001', VRMS_UPSTREAM: 'http://vrms-backend:3002', VMMS_UPSTREAM: 'http://vmms-backend:3010',
      VMMS_ANALYTICS_UPSTREAM: 'http://vmms-analytics:3011', BMS_UPSTREAM: 'https://bms.example.com',
      ALLOWED_ORIGINS: 'http://localhost:8000 , https://vrms.welinc.tech', TRUST_EDGE_PROXY: '0',
      GATEWAY_RATE_PER_SECOND: '20', GATEWAY_RATE_BURST: '40', GATEWAY_HSTS: '',
    };
    const start = (env) => {
      const args = ['run', '--rm'];
      for (const [k, v] of Object.entries(env)) if (v !== undefined) args.push('-e', `${k}=${v}`);
      const r = run('docker', [...args, IMAGE, 'nginx', '-t']);
      return { code: r.status, out: `${r.stdout}${r.stderr}` };
    };
    const good = start(base);
    check('AC-13', 'valid settings (spaces around commas) start', good.code === 0, good.out.slice(-300));
    const cases = [
      ['AUTH_UPSTREAM', undefined], ['GATEWAY_HSTS', undefined], ['ALLOWED_ORIGINS', undefined], ['TRUST_EDGE_PROXY', ''],
      ['ALLOWED_ORIGINS', 'http://localhost:8000,,http://localhost:8001'], ['ALLOWED_ORIGINS', 'http://localhost:8000,'],
      ['ALLOWED_ORIGINS', 'http://localhost:8000, http://localhost:8000'], ['ALLOWED_ORIGINS', 'http://Localhost:8000'],
      ['ALLOWED_ORIGINS', '*'], ['ALLOWED_ORIGINS', 'http://localhost:8000/app'], ['ALLOWED_ORIGINS', 'http://localhost:8000/'],
      ['ALLOWED_ORIGINS', 'ftp://localhost:8000'], ['VRMS_UPSTREAM', 'http://vrms-backend:3002/api'], ['BMS_UPSTREAM', 'http://bms-gateway:3020/'],
      ['VMMS_UPSTREAM', 'vmms-backend:3010'], ['TRUST_EDGE_PROXY', '2'], ['GATEWAY_RATE_PER_SECOND', '0'], ['GATEWAY_RATE_BURST', 'abc'],
    ];
    for (const [name, value] of cases) {
      const r = start({ ...base, [name]: value });
      check('AC-13', `${name}=${value === undefined ? '(unset)' : JSON.stringify(value)} stops the start and names it`,
        r.code !== 0 && r.out.includes(`gateway: ${name}`), `exit ${r.code}: ${r.out.split('\n').filter((l) => l.includes('gateway:')).join(' ')}`);
    }
  }

  // ---------- AC-14: one image from settings alone ----------
  {
    const config = JSON.parse(compose('config', '--format', 'json').stdout || '{}');
    check('AC-14', 'the test gateways run with no bind mounts',
      ['gateway', 'gateway-edge'].every((s) => !(config.services?.[s]?.volumes ?? []).length));
  }

  // ---------- AC-4: /health with every upstream stopped ----------
  {
    compose('stop', ...STUBS);
    const res = await request(GW, { url: '/health' });
    check('AC-4', 'GET /health answers 200 { status: ok } with every upstream stopped',
      res.status === 200 && res.body === '{"status":"ok"}' && /^application\/json/.test(res.headers['content-type'] ?? ''), brief(res));
  }
} catch (error) {
  check('setup', String(error.message ?? error), false);
} finally {
  if (!keep) compose('down', '-v', '--remove-orphans');
}

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length} passed, ${failed.length} failed`);
process.exit(failed.length ? 1 : 0);
