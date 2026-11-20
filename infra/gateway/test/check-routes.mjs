#!/usr/bin/env node
// Gateway checks for spec 0008, AC-1 to AC-21, and the Sentry tunnel of VRMS spec 0025 (AC-4, AC-5;
// labelled S-AC4 and S-AC5, the envelope DSN check included). Run from the workspace root (Node 24, Docker and openssl):
//   node infra/gateway/test/check-routes.mjs          start the harness, check, remove it
//   node infra/gateway/test/check-routes.mjs --keep   leave the harness running afterwards
// Exits non zero when any check fails.
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash, randomBytes } from 'node:crypto';
import { gzipSync } from 'node:zlib';

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
// The tunnel's two DSNs, as test/compose.yml sets them on the plain gateway (VRMS spec 0025)
const DSN_VRMS_WEB = 'https://0123456789abcdef0123456789abcdef@o1.ingest.us.sentry.io/11';
const DSN_PORTAL = 'https://fedcba9876543210fedcba9876543210@o1.ingest.us.sentry.io/12';

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

// The Sentry ingest stand in serves https with a throwaway one day cert, made here and never kept
const certDir = mkdtempSync(path.join(os.tmpdir(), 'gateway-tunnel-'));
const cert = run('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=o1.ingest.us.sentry.io',
  '-keyout', path.join(certDir, 'key.pem'), '-out', path.join(certDir, 'cert.pem')]);
if (cert.status !== 0) {
  console.error(`openssl could not make the test cert: ${cert.error?.message ?? cert.stderr}`);
  process.exit(1);
}
process.env.TUNNEL_CERT_DIR = certDir;

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
    return probes.every((r) => r.status === 200) && logsOf('sentry-ingest').includes('listening');
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
        res.headers['access-control-allow-headers'] === 'Authorization, Content-Type, X-Request-Id, sentry-trace, baggage' &&
        res.headers['access-control-max-age'] === '600', JSON.stringify(res.headers));
    const bad = await request(GW, { method: 'OPTIONS', url: `/vrms/x?m=${m9}`, headers: { Origin: UNLISTED, ...pre } });
    check('AC-9', 'an unlisted preflight answers 204 with no Access-Control-* header', bad.status === 204 && corsHeaderNames(bad).length === 0,
      `${bad.status} ${corsHeaderNames(bad).join()}`);
    check('AC-9', 'preflights reach no upstream', !logsOf('vrms-backend').includes(m9));
  }

  // ---------- VRMS spec 0025, AC-4, AC-5: the Sentry tunnel ----------
  {
    const TUNNEL = '/monitoring/vrms-web';
    const envelope = (dsn, item = '{}') => `${JSON.stringify({ event_id: marker(), dsn })}\n{"type":"event"}\n${item}`;
    const right = envelope(DSN_VRMS_WEB);
    const sha = (body) => createHash('sha256').update(body).digest('hex');
    const reached = (body) => logsOf('sentry-ingest').includes(`sha256=${sha(body)}`);

    const mt = marker();
    const pre = await request(GW, { method: 'OPTIONS', url: `${TUNNEL}?m=${mt}`, headers: { Origin: LISTED, 'Access-Control-Request-Method': 'POST' } });
    check('S-AC5', 'OPTIONS answers 204 with CORS for a listed origin',
      pre.status === 204 && pre.headers['access-control-allow-origin'] === LISTED &&
        pre.headers['access-control-allow-methods'] === 'POST, OPTIONS', JSON.stringify(pre.headers));
    const get = await request(GW, { url: `${TUNNEL}?m=${mt}`, headers: { Origin: LISTED } });
    check('S-AC5', 'GET answers the JSON 405 with Allow: POST, OPTIONS',
      isGatewayError(get, 405, 'METHOD_NOT_ALLOWED') && get.headers.allow === 'POST, OPTIONS', brief(get));
    check('S-AC5', 'OPTIONS and GET never reach Sentry', !logsOf('sentry-ingest').includes(mt));

    const planted = {
      Origin: LISTED, 'Content-Type': 'text/plain;charset=UTF-8', Cookie: 'welinc_sso=secretcookie',
      Authorization: 'Bearer secrettoken', 'X-Sentry-Auth': 'Sentry sentry_key=secretkey', 'X-Forwarded-For': '6.6.6.6',
      'X-Real-IP': '6.6.6.6', Forwarded: 'for=6.6.6.6', Referer: 'http://localhost:8001/reset?code=topsecret',
      'Accept-Encoding': 'gzip', 'X-Request-Id': 'tunnel-1', 'User-Agent': 'tunnel-test/1',
    };
    const res = await request(GW, { method: 'POST', url: `${TUNNEL}?m=${mt}`, headers: planted, body: right });
    const sent = res.json?.headers ?? {};
    check('S-AC4', 'POST /monitoring/vrms-web with its own DSN reaches its project, without the query',
      res.status === 200 && res.json?.service === 'sentry-ingest' && res.json?.url === '/api/11/envelope/' &&
        res.json?.sha256 === sha(right), brief(res));
    check('S-AC4', 'Sentry is called by its own host name', sent.host === 'o1.ingest.us.sentry.io', sent.host);
    check('S-AC5', 'Sentry gets no cookie, Authorization, client address, page address or request id',
      ['cookie', 'authorization', 'x-sentry-auth', 'x-forwarded-for', 'x-real-ip', 'forwarded', 'referer', 'accept-encoding', 'x-request-id']
        .every((h) => !(h in sent)), JSON.stringify(sent));
    check('S-AC5', 'Origin, User-Agent and Content-Type pass through to Sentry',
      sent.origin === LISTED && sent['content-type'] === 'text/plain;charset=UTF-8' && sent['user-agent'] === 'tunnel-test/1',
      JSON.stringify(sent));
    check('S-AC5', "Sentry's Retry-After and X-Sentry-Rate-Limits come back",
      res.headers['retry-after'] === '7' && res.headers['x-sentry-rate-limits'] === '60:error:organization', JSON.stringify(res.headers));
    check('S-AC5', 'a listed origin gets exactly one allow origin header on the POST, and the gateway request id',
      headerValues(res, 'access-control-allow-origin').join() === LISTED && headerValues(res, 'x-request-id').join() === 'tunnel-1' &&
        headerValues(res, 'vary').join() === 'Origin', JSON.stringify(res.raw));

    // A body with binary items (invalid UTF-8 included) and a \r\n header line reaches Sentry byte for byte
    const binary = Buffer.concat([
      Buffer.from(`${JSON.stringify({ dsn: DSN_VRMS_WEB })}\r\n{"type":"attachment","length":512}\n`),
      randomBytes(512), Buffer.from([0x00, 0xff, 0xfe, 0xc3, 0x28, 0x0a]),
    ]);
    const bin = await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED }, body: binary });
    check('S-AC5', 'a binary envelope reaches Sentry byte for byte',
      bin.status === 200 && bin.json?.bytes === binary.length && bin.json?.sha256 === sha(binary), brief(bin));

    const portalRight = envelope(DSN_PORTAL);
    const portal = await request(GW, { method: 'POST', url: '/monitoring/portal', headers: { Origin: 'http://localhost:8000' }, body: portalRight });
    check('S-AC4', 'POST /monitoring/portal with its own DSN reaches the portal project',
      portal.json?.url === '/api/12/envelope/' && portal.json?.sha256 === sha(portalRight), brief(portal));

    // Every body that isn't this route's own DSN: 403 TUNNEL_REJECTED, nothing reaches Sentry
    const key = DSN_VRMS_WEB.slice(8, 40);
    const header = (h) => `${h}\n{"type":"event"}\n{"m":"${marker()}"}`;
    const rejects = [
      ['another project on the same host', envelope('https://' + key + '@o1.ingest.us.sentry.io/99')],
      ["another organization's host", envelope('https://' + key + '@o2.ingest.us.sentry.io/11')],
      ["the other route's DSN", envelope(DSN_PORTAL)],
      ['a different key for the same project', envelope('https://' + 'a'.repeat(32) + '@o1.ingest.us.sentry.io/11')],
      ['an uppercase key', envelope(DSN_VRMS_WEB.replace(key, key.toUpperCase()))],
      ['a port', envelope(DSN_VRMS_WEB.replace('.io/', '.io:443/'))],
      ['a trailing slash', envelope(`${DSN_VRMS_WEB}/`)],
      ['a trailing newline in the dsn', envelope(`${DSN_VRMS_WEB}\n`)],
      ['a password', envelope(DSN_VRMS_WEB.replace('@', ':secret@'))],
      ['http instead of https', envelope(DSN_VRMS_WEB.replace('https:', 'http:'))],
      ['a duplicate dsn key', header(`{"dsn":"${DSN_VRMS_WEB}","dsn":"https://${key}@o1.ingest.us.sentry.io/99"}`)],
      ['an escaped dsn key', header(`{"d\\u0073n":"https://${key}@o1.ingest.us.sentry.io/99","x":"${DSN_VRMS_WEB}"}`)],
      ['no dsn', header(`{"event_id":"${marker()}"}`)],
      ['a dsn that is not a string', header('{"dsn":11}')],
      ['a header that is an array', header(`["dsn","${DSN_VRMS_WEB}"]`)],
      ['no newline in the first 8 KB', header(`{"dsn":"${DSN_VRMS_WEB}","pad":"${'a'.repeat(9000)}"}`)],
      ['a header that is not JSON', header(`dsn "dsn" ${DSN_VRMS_WEB}`)],
      ['an empty body', ''],
    ];
    for (const [name, body] of rejects) {
      const r = await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED }, body });
      check('S-AC5', `${name} answers 403 TUNNEL_REJECTED with CORS and never reaches Sentry`,
        isGatewayError(r, 403, 'TUNNEL_REJECTED') && headerValues(r, 'access-control-allow-origin').join() === LISTED &&
          /^[A-Za-z0-9._-]{1,64}$/.test(r.headers?.['x-request-id'] ?? '') && !(body && reached(body)), brief(r));
      await sleep(1000); // stay under the tunnel limit of 1 a second
    }
    await sleep(1000);
    const gz = gzipSync(right);
    const gzRes = await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED, 'Content-Encoding': 'gzip' }, body: gz });
    check('S-AC5', 'a gzip body (even with the right DSN) answers 403 TUNNEL_REJECTED and never reaches Sentry',
      isGatewayError(gzRes, 403, 'TUNNEL_REJECTED') && !reached(gz), brief(gzRes));
    await sleep(1000);
    const identity = envelope(DSN_VRMS_WEB);
    const idRes = await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED, 'Content-Encoding': 'identity' }, body: identity });
    check('S-AC5', 'Content-Encoding: identity with the right DSN is forwarded', idRes.status === 200 && reached(identity), brief(idRes));

    await sleep(1000);
    const unlisted = await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: UNLISTED }, body: envelope(DSN_VRMS_WEB) });
    check('S-AC5', 'an unlisted origin gets no Access-Control-* header', unlisted.status === 200 && corsHeaderNames(unlisted).length === 0,
      corsHeaderNames(unlisted).join());
    const big = await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED }, body: Buffer.alloc(2 * MB) });
    check('S-AC5', 'a 2 MB body answers the JSON 413', big.error !== undefined || isGatewayError(big, 413, 'PAYLOAD_TOO_LARGE'), brief(big));
    await sleep(1200);
    const full = Buffer.concat([Buffer.from(`${JSON.stringify({ dsn: DSN_VRMS_WEB })}\n`), Buffer.alloc(MB - 100, 0x61)]);
    const fullRes = await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED }, body: full });
    check('S-AC5', 'a body just under 1 MB is checked in memory and forwarded whole',
      fullRes.status === 200 && fullRes.json?.bytes === full.length && fullRes.json?.sha256 === sha(full), brief(fullRes));
    for (const p of ['/monitoring/vrms-web/', '/monitoring/other', '/monitoring', '/_tunnel/vrms-web', '/_tunnel/portal']) {
      const other = await request(GW, { method: 'POST', url: p, body: right });
      check('S-AC4', `${p} is not a public route`, isGatewayError(other, 404, 'NOT_FOUND'), brief(other));
    }

    // One access log line per report, and none of the body in the log
    await sleep(1000);
    const logged = envelope(DSN_VRMS_WEB, '{"secret":"bodysecret"}');
    await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED, 'X-Request-Id': 'tunnel-log-1' }, body: logged });
    await sleep(1000);
    const rejectedLogged = envelope('https://' + key + '@o1.ingest.us.sentry.io/99', '{"secret":"bodysecret"}');
    await request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED, 'X-Request-Id': 'tunnel-log-2' }, body: rejectedLogged });
    await sleep(500);
    const lines = logsOf('gateway').split('\n').map((l) => { try { return JSON.parse(l); } catch { return undefined; } }).filter(Boolean);
    const forwardedLines = lines.filter((l) => l.request_id === 'tunnel-log-1');
    const rejectedLines = lines.filter((l) => l.request_id === 'tunnel-log-2');
    check('S-AC5', 'a forwarded report logs one line, with Sentry as the upstream',
      forwardedLines.length === 1 && forwardedLines[0].status === 200 && forwardedLines[0].upstream !== '', JSON.stringify(forwardedLines));
    check('S-AC5', 'a refused report logs one line with status 403 and no upstream',
      rejectedLines.length === 1 && rejectedLines[0].status === 403 && rejectedLines[0].upstream === '', JSON.stringify(rejectedLines));
    check('S-AC5', 'no envelope body reaches the gateway log', !/bodysecret|secretkey/.test(logsOf('gateway')));

    await sleep(1500); // let the tunnel's bucket refill after the posts above
    const burst = await Promise.all(Array.from({ length: 30 }, () => request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED }, body: right })));
    const limited = burst.filter((r) => r.status === 429);
    const passed = burst.filter((r) => r.status === 200).length;
    check('S-AC5', 'a burst past 1 a second (burst 10) gets the JSON 429',
      limited.length > 0 && passed <= 12 && limited.every((r) => isGatewayError(r, 429, 'RATE_LIMITED')),
      `${passed} passed, ${limited.length} limited`);
    await sleep(1500);
    const refusedBurst = await Promise.all(Array.from({ length: 30 }, () => request(GW, { method: 'POST', url: TUNNEL, headers: { Origin: LISTED }, body: rejectedLogged })));
    check('S-AC5', 'refused reports count against the tunnel limit too',
      refusedBurst.some((r) => r.status === 429) && refusedBurst.filter((r) => r.status === 403).length <= 12,
      refusedBurst.map((r) => r.status).join(','));

    const off = await Promise.all(['/monitoring/vrms-web', '/monitoring/portal'].map((url) =>
      request(EDGE, { method: 'POST', url, headers: { Origin: LISTED }, body: right })));
    check('S-AC5', 'with the tunnel settings blank both routes answer the JSON 404',
      off.every((r) => isGatewayError(r, 404, 'NOT_FOUND')), off.map(brief).join(' / '));
    await sleep(500);
    check('S-AC5', 'tunnel secrets never reach the gateway log', !/topsecret|secrettoken|secretcookie/.test(logsOf('gateway')));
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
    // VRMS feature 69 (first ZAP scan): one nosniff on every answer, whatever the upstream sends
    check('AC-21', 'proxied, preflight, error and /health answers carry exactly one nosniff',
      off.every((r) => headerValues(r, 'x-content-type-options').join() === 'nosniff'),
      off.map((r) => headerValues(r, 'x-content-type-options').join('|')).join(' / '));
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
      ALLOWED_ORIGINS: 'http://localhost:8000 , https://vrms.welinc.app', TRUST_EDGE_PROXY: '0',
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

    // VRMS spec 0025: the tunnel's two DSNs start both set or both blank, and refuse a half set or bad one
    const tunnel = { SENTRY_DSN_VRMS_WEB: 'https://' + 'a1'.repeat(16) + '@o4507.ingest.us.sentry.io/45',
      SENTRY_DSN_PORTAL: 'https://' + 'b2'.repeat(16) + '@o4507.ingest.sentry.io/46' };
    const on = start({ ...base, ...tunnel });
    check('S-AC5', 'valid tunnel settings start and nginx -t passes on the built image', on.code === 0 && on.out.includes('Sentry tunnel on'),
      on.out.slice(-300));
    check('S-AC5', 'blank tunnel settings start with the tunnel off', good.out.includes('Sentry tunnel off'), good.out.slice(-300));
    const okKey = 'a1'.repeat(16);
    const tunnelCases = [
      ['SENTRY_DSN_PORTAL', undefined], ['SENTRY_DSN_VRMS_WEB', ''],
      ['SENTRY_DSN_VRMS_WEB', `https://${okKey.toUpperCase()}@o4507.ingest.us.sentry.io/45`],
      ['SENTRY_DSN_VRMS_WEB', `https://${okKey}@o4507.ingest.us.sentry.io:443/45`],
      ['SENTRY_DSN_VRMS_WEB', `https://${okKey}@o4507.ingest.us.sentry.io/45/`],
      ['SENTRY_DSN_VRMS_WEB', `https://${okKey}@o4507.ingest.us.sentry.io/x/45`],
      ['SENTRY_DSN_VRMS_WEB', `https://${okKey}@o4507.ingest.us.sentry.io/45?x=1`],
      ['SENTRY_DSN_VRMS_WEB', `http://${okKey}@o4507.ingest.us.sentry.io/45`],
      ['SENTRY_DSN_VRMS_WEB', `https://${okKey}:secret@o4507.ingest.us.sentry.io/45`],
      ['SENTRY_DSN_VRMS_WEB', `https://${okKey}@o4507.ingest.us.sentry.io.evil.com/45`],
      ['SENTRY_DSN_PORTAL', `https://${okKey}@evil.example.com/46`],
      ['SENTRY_DSN_PORTAL', `https://${okKey}@o4507.ingest.us.sentry.io/0`],
      ['SENTRY_DSN_PORTAL', 'https://short@o4507.ingest.us.sentry.io/46'],
    ];
    for (const [name, value] of tunnelCases) {
      const r = start({ ...base, ...tunnel, [name]: value });
      check('S-AC5', `${name}=${value === undefined ? '(unset)' : JSON.stringify(value)} with the other set stops the start and names it`,
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
  if (!keep) {
    compose('down', '-v', '--remove-orphans');
    rmSync(certDir, { recursive: true, force: true });
  }
}

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length} passed, ${failed.length} failed`);
process.exit(failed.length ? 1 : 0);
