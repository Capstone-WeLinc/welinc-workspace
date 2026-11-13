#!/usr/bin/env node
// Checks one system against the shared services contract (suite spec 0014, AC-12 to AC-14):
// live checks through the gateway (login, fleet) and a static scan of the system's repos for
// leftovers of the old login. It reads no .env value and needs no client key: every token it uses
// comes from signing in a seed account (docs/integration/seed-accounts.md).
//
// Usage (from the workspace root, with the stack running):
//   node scripts/check-system.mjs vrms                 every group that applies
//   node scripts/check-system.mjs vmms --static-only   only the scan of the repos on disk
//   node scripts/check-system.mjs bms --live-only      only the live checks
//   node scripts/check-system.mjs bms --fleet          only the fleet group (--login: only login)
//   --api <url>       the gateway (default http://localhost:3000)
//   --portal <url>    the portal (default http://localhost:8000)
//   --accounts <file> JSON that overrides seed logins, for example
//                     { "vmms.ops": { "email": "...", "password": "..." } }
//
// Exit codes: 0 every check passed, 1 a check failed, 2 the stack doesn't answer at all.
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { basename, dirname, extname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

/** What the checker knows about each system. Paths are the ones contract 0001 and the guides fix. */
export const SYSTEMS = {
  vrms: {
    code: 'VRMS',
    prefix: '/vrms',
    // Any VRMS role opens it, and it runs the 30 s account check like every protected route
    protectedPath: '/vrms/permissions/me',
    account: 'vrms.chief',
    repos: ['welinc-backend-vrms', 'welinc-web-vrms', 'welinc-web-portal'],
  },
  vmms: {
    code: 'VMMS',
    prefix: '/vmms',
    protectedPath: '/vmms/vehicles',
    account: 'vmms.ops',
    repos: [
      'welinc-backend-vmms',
      'welinc-backend-vmms-analytics-ai',
      'welinc-web-vmms',
      'welinc-mobile-vrms_vmms',
    ],
  },
  bms: {
    code: 'BMS',
    prefix: '/bms',
    // Served by dispatch for Admin and Operations; it needs no fleet answer, so login checks
    // don't fail just because VMMS is down
    protectedPath: '/bms/dispatch/assignments',
    account: 'bms.ops',
    repos: ['welinc-backend-bms', 'welinc-backend-bms-analytics-ai', 'welinc-web-bms'],
  },
};

/** Seed logins that need no emailed code (docs/integration/seed-accounts.md). */
export const DEFAULT_ACCOUNTS = {
  'vrms.chief': { email: 'vrms.chief@welinc.com', password: 'chief1234' },
  'vmms.ops': { email: 'vmms.ops@welinc.com', password: 'ops1234' },
  'vmms.mech': { email: 'vmms.mech@welinc.com', password: 'mechanic1234' },
  'bms.ops': { email: 'bms.ops@welinc.com', password: 'ops1234' },
  'bms.cs': { email: 'bms.cs@welinc.com', password: 'cs1234' },
  'driver.ramon': { email: 'driver.ramon@welinc.com', password: 'driver1234' },
  'multi.lead': { email: 'multi.lead@welinc.com', password: 'chief1234' },
};

/** How long a system may keep honoring a token after logout (contract 0001 section 6). */
const SESSION_END_LIMIT_MS = 31_000;
const BIG_BODY_BYTES = 5 * 1024 * 1024;

// ---------------------------------------------------------------- static scan

/** Folders and files the scan never opens. `.env` files hold values, so only `.env.example` is read. */
const SKIP_DIRS = new Set(['node_modules', 'dist', 'build', '.git', 'coverage', '.expo', '.next', '.turbo']);
const LOCKFILES = new Set(['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb', 'npm-shrinkwrap.json']);
const SOURCE_EXTENSIONS = new Set([
  '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.json', '.yml', '.yaml', '.prisma', '.sh', '.html', '.conf', '.sql',
]);
/** Files where a line starting with `#` is a comment. */
const HASH_COMMENT_EXTENSIONS = new Set(['.yml', '.yaml', '.sh', '.conf', '']);
const MAX_FILE_BYTES = 2 * 1024 * 1024;

export const ALLOW_MARKER = /\/\/\s*check-system:\s*allow\s+(.+?)\s*$/;

/**
 * The leftovers of the old login (AC-13). Each `test` gets the lines of the file and an index, so a
 * rule can look at the next lines too.
 */
export const RULES = [
  { name: 'JWT_SECRET (shared secret)', test: (l) => l[0].includes('JWT_SECRET') },
  { name: 'AUTH_DATABASE_URL (reads the auth database)', test: (l) => l[0].includes('AUTH_DATABASE_URL') },
  { name: 'BMS_PARTNER_DATABASE_URL', test: (l) => l[0].includes('BMS_PARTNER_DATABASE_URL') },
  { name: '5433/welinc_db (the old Capstone 1 database)', test: (l) => /5433\/welinc_db(?!\w)/.test(l[0]) },
  { name: 'HS256 (shared secret tokens)', test: (l) => l[0].includes('HS256') },
  { name: 'jwt-decode (reads tokens in the browser)', test: (l) => l[0].includes('jwt-decode') },
  { name: 'X-VMMS-Client header', test: (l) => /x-vmms-client/i.test(l[0]) },
  {
    name: 'token in localStorage or sessionStorage',
    test: (l) => /\b(localStorage|sessionStorage)\b/.test(l[0]) && l.slice(0, 3).some((x) => /token/i.test(x)),
  },
  {
    name: 'token read from the URL',
    test: (l) => /searchParams\.get\(\s*['"`]token['"`]\s*\)/.test(l[0]) || l[0].includes('?token='),
  },
  { name: 'SEMAPHORE_ (SMS)', test: (l) => l[0].includes('SEMAPHORE_') },
  {
    name: 'calls a bearer admin route AC-33 removes',
    test: (l) => /\/auth\/(users|deletion-requests)(?![\w-])/.test(l[0]),
  },
];

function isComment(line, ext) {
  const t = line.trim();
  if (t.startsWith('//') || t.startsWith('/*') || t.startsWith('*') || t.startsWith('<!--')) return true;
  return t.startsWith('#') && HASH_COMMENT_EXTENSIONS.has(ext);
}

/** Scans one file's text. Returns the hits and the lines a `check-system: allow` marker let through. */
export function scanText(text, ext = '.ts') {
  const lines = text.split(/\r?\n/);
  const hits = [];
  const allowed = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (isComment(line, ext)) continue;
    const window = lines.slice(i, i + 3);
    const rule = RULES.find((r) => r.test(window));
    if (!rule) continue;
    const marker = line.match(ALLOW_MARKER);
    if (marker) allowed.push({ line: i + 1, rule: rule.name, reason: marker[1] });
    else hits.push({ line: i + 1, rule: rule.name });
  }
  return { hits, allowed };
}

function wantsFile(name) {
  if (LOCKFILES.has(name) || name.endsWith('.md')) return false;
  if (name === '.env.example') return true;
  if (name === '.env' || name.startsWith('.env.')) return false;
  if (name.startsWith('Dockerfile')) return true;
  return SOURCE_EXTENSIONS.has(extname(name));
}

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) yield* walk(join(dir, entry.name));
    } else if (entry.isFile() && wantsFile(entry.name)) {
      yield join(dir, entry.name);
    }
  }
}

/** Scans a repo folder on disk. */
export function scanRepo(dir) {
  const hits = [];
  const allowed = [];
  let files = 0;
  for (const file of walk(dir)) {
    if (statSync(file).size > MAX_FILE_BYTES) continue;
    files++;
    const name = basename(file);
    const ext = name.startsWith('Dockerfile') || name === '.env.example' ? '' : extname(name);
    const result = scanText(readFileSync(file, 'utf8'), ext);
    const where = relative(ROOT, file).split('\\').join('/');
    for (const h of result.hits) hits.push({ ...h, file: where });
    for (const a of result.allowed) allowed.push({ ...a, file: where });
  }
  return { files, hits, allowed };
}

// ---------------------------------------------------------------- cookies and http

/** Reads one Set-Cookie line. Names keep their case; attribute names don't. */
export function parseSetCookie(line) {
  const [pair, ...attrs] = line.split(';');
  const eq = pair.indexOf('=');
  const cookie = {
    name: pair.slice(0, eq).trim(),
    value: pair.slice(eq + 1).trim(),
    path: '/',
    httpOnly: false,
    secure: false,
    sameSite: null,
    expired: false,
  };
  for (const attr of attrs) {
    const [rawKey, ...rest] = attr.split('=');
    const key = rawKey.trim().toLowerCase();
    const value = rest.join('=').trim();
    if (key === 'path') cookie.path = value || '/';
    else if (key === 'httponly') cookie.httpOnly = true;
    else if (key === 'secure') cookie.secure = true;
    else if (key === 'samesite') cookie.sameSite = value;
    else if (key === 'max-age' && Number(value) <= 0) cookie.expired = true;
    else if (key === 'expires' && Date.parse(value) <= Date.now()) cookie.expired = true;
  }
  if (cookie.value === '') cookie.expired = true;
  return cookie;
}

/** A small cookie jar for one pretend browser. Every request goes to the one gateway host. */
export class CookieJar {
  constructor() {
    this.cookies = new Map();
  }

  store(setCookies) {
    for (const line of setCookies) {
      const c = parseSetCookie(line);
      if (c.expired) this.cookies.delete(c.name);
      else this.cookies.set(c.name, c);
    }
  }

  get(name) {
    return this.cookies.get(name)?.value ?? null;
  }

  header(path) {
    const sent = [];
    for (const c of this.cookies.values()) {
      const p = c.path.endsWith('/') ? c.path : `${c.path}/`;
      if (path === c.path || path.startsWith(p)) sent.push(`${c.name}=${c.value}`);
    }
    return sent.join('; ');
  }
}

async function http(url, { method = 'GET', headers = {}, body, jar, timeoutMs = 15_000 } = {}) {
  const target = new URL(url);
  const sent = { ...headers };
  const cookie = jar?.header(target.pathname);
  if (cookie && !sent.Cookie) sent.Cookie = cookie;
  const res = await fetch(target, {
    method,
    headers: sent,
    body,
    redirect: 'manual',
    signal: AbortSignal.timeout(timeoutMs),
  });
  const setCookies = res.headers.getSetCookie();
  jar?.store(setCookies);
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    // Not JSON: an HTML page or an empty body
  }
  return { status: res.status, location: res.headers.get('location'), headers: res.headers, setCookies, json, text };
}

const bearer = (token) => ({ Authorization: `Bearer ${token}` });
const jsonPost = (origin) => ({ 'Content-Type': 'application/json', ...(origin ? { Origin: origin } : {}) });

/** The payload of a JWT, without checking anything. */
export function tokenPayload(token) {
  return JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'));
}

/** The same token with one signature character changed, so its signature no longer matches. */
export function tamper(token) {
  const [head, body, sig] = token.split('.');
  const i = Math.floor(sig.length / 2);
  const swapped = sig[i] === 'A' ? 'B' : 'A';
  return `${head}.${body}.${sig.slice(0, i)}${swapped}${sig.slice(i + 1)}`;
}

/** Why an answer wasn't the one expected, short enough for one line. */
function answered(res) {
  const code = res.json?.code ?? res.json?.error;
  const where = res.location ? ` to ${res.location.slice(0, 120)}` : '';
  return `answered ${res.status}${code ? ` ${code}` : ''}${where}`;
}

// ---------------------------------------------------------------- report

class Report {
  constructor() {
    this.groups = new Map();
    this.current = null;
  }

  start(group, title) {
    this.current = group;
    if (!this.groups.has(group)) this.groups.set(group, { ok: 0, fail: 0, skip: 0 });
    console.log(`\n== ${title}`);
  }

  ok(label) {
    this.groups.get(this.current).ok++;
    console.log(`ok    ${label}`);
  }

  fail(label, reason) {
    this.groups.get(this.current).fail++;
    console.log(`FAIL  ${label}: ${reason}`);
  }

  skip(label, reason) {
    this.groups.get(this.current).skip++;
    console.log(`skip  ${label}: ${reason}`);
  }

  note(text) {
    console.log(`      ${text}`);
  }

  /** Runs one check: ok when `fn` returns without throwing, FAIL with the thrown message. */
  async check(label, fn) {
    try {
      const skipped = await fn();
      if (typeof skipped === 'string') this.skip(label, skipped);
      else this.ok(label);
      return true;
    } catch (error) {
      this.fail(label, error instanceof Error ? error.message : String(error));
      return false;
    }
  }

  get failed() {
    return [...this.groups.values()].some((g) => g.fail > 0);
  }

  summary() {
    console.log('\n== Summary');
    for (const [name, g] of this.groups) {
      const parts = [`${g.ok} ok`, `${g.fail} failed`];
      if (g.skip) parts.push(`${g.skip} skipped`);
      console.log(`${name.padEnd(7)} ${parts.join(', ')}`);
    }
  }
}

class Failure extends Error {}
const expect = (cond, reason) => {
  if (!cond) throw new Failure(reason);
};

// ---------------------------------------------------------------- sign in flows

/**
 * Signs a seed account in at the portal (POST /auth/login with the portal's Origin), the way the
 * portal does. Returns a jar holding the SSO cookie. One login per account per run, since
 * /auth/login allows 10 a minute per address.
 */
async function portalLogin(ctx, key) {
  const cached = ctx.sso.get(key);
  if (cached) return cached;
  const account = ctx.accounts[key];
  const jar = new CookieJar();
  const res = await http(`${ctx.api}/auth/login`, {
    method: 'POST',
    headers: jsonPost(ctx.portalOrigin),
    body: JSON.stringify({ email: account.email, password: account.password }),
    jar,
  });
  if (res.status === 429) {
    throw new Failure('/auth/login allows 10 sign ins a minute from one address; wait a minute and run again');
  }
  expect(res.status === 200, `portal sign in as ${account.email} ${answered(res)}`);
  expect(!res.json?.challengeId, `${account.email} was asked for an emailed code; use an account that needs none`);
  const entry = { jar, answer: res.json };
  ctx.sso.set(key, entry);
  return entry;
}

/** `logout` ended the account's whole web session, so its next use signs in again. */
function forgetLogin(ctx, key) {
  ctx.sso.delete(key);
}

/**
 * The browser side of a system login: session/start, /auth/authorize with the SSO cookie, the
 * callback. Each step can be reported through `step(label, fn)`. Returns what the callback set.
 */
async function systemLogin(ctx, sysKey, accountKey, step = (_label, fn) => fn()) {
  const sys = SYSTEMS[sysKey];
  const { jar } = await portalLogin(ctx, accountKey);
  const callbackUrl = `${ctx.api}${sys.prefix}/session/callback`;
  const cookiePrefix = ctx.api.startsWith('https:') ? '__Secure-' : '';
  const out = { jar, sys };

  await step(`${sys.prefix}/session/start redirects to /auth/authorize with client_id=${sysKey}, S256 and the exact callback`, async () => {
    const res = await http(`${ctx.api}${sys.prefix}/session/start`, { jar });
    expect(res.status === 302 && res.location, `${answered(res)}, not a 302`);
    const to = new URL(res.location, ctx.api);
    const q = to.searchParams;
    expect(to.pathname === '/auth/authorize', `redirects to ${to.pathname}, not /auth/authorize`);
    expect(q.get('client_id') === sysKey, `client_id is ${q.get('client_id')}`);
    expect(q.get('response_type') === 'code', `response_type is ${q.get('response_type')}`);
    expect(q.get('code_challenge_method') === 'S256', `code_challenge_method is ${q.get('code_challenge_method')}`);
    expect(q.get('code_challenge'), 'no code_challenge');
    expect(q.get('redirect_uri') === callbackUrl, `redirect_uri is ${q.get('redirect_uri')}, expected ${callbackUrl}`);
    const state = q.get('state');
    expect(state, 'no state');
    const loginCookie = `${cookiePrefix}${sysKey}_login_${state.slice(0, 8)}`;
    expect(jar.get(loginCookie), `no ${loginCookie} cookie was set`);
    out.authorizeUrl = to.href;
    out.state = state;
  });

  await step('/auth/authorize answers the callback (code and the same state, or an error)', async () => {
    const res = await http(out.authorizeUrl, { jar });
    expect(res.status === 302 && res.location, `${answered(res)}, not a 302`);
    const to = new URL(res.location, ctx.api);
    expect(`${to.origin}${to.pathname}` === callbackUrl, `redirects to ${to.origin}${to.pathname}, not the callback`);
    expect(to.searchParams.get('state') === out.state, 'the state came back changed');
    out.authorizeAnswer = to;
  });

  await step(`the callback sets ${cookiePrefix}${sysKey}_rt (HttpOnly, path ${sys.prefix}/session)`, async () => {
    const res = await http(out.authorizeAnswer.href, { jar });
    expect(res.status === 302 && res.location, `${answered(res)}, not a 302`);
    out.callbackLocation = res.location;
    const to = new URL(res.location, ctx.api);
    if (to.origin === ctx.portalOrigin && to.searchParams.get('error')) {
      out.portalError = to;
      return 'the callback sent the browser to the portal error page (checked below)';
    }
    const name = `${cookiePrefix}${sysKey}_rt`;
    const set = res.setCookies.map(parseSetCookie).find((c) => c.name === name);
    expect(set, `no ${name} cookie (cookies set: ${res.setCookies.map((l) => l.split('=')[0]).join(', ') || 'none'})`);
    expect(set.httpOnly, `${name} is not HttpOnly`);
    expect(set.path === `${sys.prefix}/session`, `${name} has path ${set.path}`);
    if (cookiePrefix) expect(set.secure, `${name} is not Secure`);
    out.webOrigin = to.origin;
    out.rtName = name;
  });
  return out;
}

/** A refresh through the system's cookie route, with the web app's Origin. */
function refresh(ctx, login, cookie) {
  return http(`${ctx.api}${login.sys.prefix}/session/refresh`, {
    method: 'POST',
    headers: { ...jsonPost(login.webOrigin), ...(cookie ? { Cookie: cookie } : {}) },
    body: '{}',
    jar: cookie ? undefined : login.jar,
  });
}

/** A user access token for a system, by the full web flow, or a thrown reason. */
async function accessToken(ctx, sysKey, accountKey) {
  const login = await systemLogin(ctx, sysKey, accountKey);
  if (login.portalError) {
    throw new Failure(`${ctx.accounts[accountKey].email} can't open ${sysKey}: ${login.portalError.search}`);
  }
  const res = await refresh(ctx, login);
  expect(res.status === 200 && res.json?.accessToken, `refresh ${answered(res)}`);
  return res.json.accessToken;
}

async function isUp(ctx, path) {
  try {
    return (await http(`${ctx.api}${path}`, { timeoutMs: 5_000 })).status === 200;
  } catch {
    return false;
  }
}

/** Signs in an account that may only use the phone app and expects the portal's APP_NOT_ALLOWED page. */
async function expectNotAllowed(ctx, sysKey, accountKey) {
  const login = await systemLogin(ctx, sysKey, accountKey);
  const answer = login.authorizeAnswer;
  expect(answer.searchParams.get('error') === 'access_denied', `/auth/authorize sent error=${answer.searchParams.get('error')}`);
  expect(
    answer.searchParams.get('error_description') === 'APP_NOT_ALLOWED',
    `/auth/authorize sent error_description=${answer.searchParams.get('error_description')}`,
  );
  const end = login.portalError;
  expect(end, `the callback went to ${login.callbackLocation}, not the portal`);
  expect(end.pathname === '/', `the portal path is ${end.pathname}`);
  expect(end.searchParams.get('error') === 'APP_NOT_ALLOWED', `the portal got error=${end.searchParams.get('error')}`);
  expect(end.searchParams.get('system') === SYSTEMS[sysKey].code, `the portal got system=${end.searchParams.get('system')}`);
}

// ---------------------------------------------------------------- groups

async function loginGroup(ctx, report, sysKey) {
  const sys = SYSTEMS[sysKey];
  report.start('login', `${sys.code} login (through ${ctx.api})`);
  const protectedUrl = `${ctx.api}${sys.protectedPath}`;

  await report.check(`${sys.prefix}/health answers 200 with checks`, async () => {
    const res = await http(`${ctx.api}${sys.prefix}/health`);
    expect(res.status === 200, answered(res));
    expect(res.json?.checks && typeof res.json.checks === 'object', 'the answer has no checks');
  });

  // The main account's web flow, one check per step
  let login;
  let token;
  const flowOk = await report.check(`${ctx.accounts[sys.account].email} signs in at the portal`, () =>
    portalLogin(ctx, sys.account),
  );
  if (flowOk) {
    try {
      login = await systemLogin(ctx, sysKey, sys.account, async (label, fn) => {
        if (!(await report.check(label, fn))) throw new Failure('stop');
      });
    } catch {
      login = null;
    }
  }
  if (login?.portalError) {
    report.fail('the sign in reaches the system', `the callback sent the browser to ${login.callbackLocation}`);
    login = null;
  }
  if (login) {
    await report.check(`${sys.prefix}/session/refresh without the web app's Origin answers 403 CSRF_REJECTED`, async () => {
      const res = await http(`${ctx.api}${sys.prefix}/session/refresh`, {
        method: 'POST',
        headers: jsonPost(null),
        body: '{}',
        jar: login.jar,
      });
      expect(res.status === 403 && res.json?.code === 'CSRF_REJECTED', answered(res));
    });
    await report.check(`${sys.prefix}/session/refresh answers an access token with aud ${sys.code}`, async () => {
      const res = await refresh(ctx, login);
      expect(res.status === 200 && res.json?.accessToken, answered(res));
      const aud = tokenPayload(res.json.accessToken).aud;
      expect(aud === sys.code, `aud is ${JSON.stringify(aud)}`);
      token = res.json.accessToken;
    });
  }
  if (token) {
    await report.check(`the token opens ${sys.protectedPath}`, async () => {
      const res = await http(protectedUrl, { headers: bearer(token) });
      expect(res.status === 200, answered(res));
    });
  }

  await report.check(`${sys.protectedPath} answers 401 with no token`, async () => {
    const res = await http(protectedUrl);
    expect(res.status === 401, answered(res));
  });
  await report.check(`${sys.protectedPath} answers 401 with a tampered token`, async () => {
    if (!token) return 'no token to tamper with (the sign in failed above)';
    const res = await http(protectedUrl, { headers: bearer(tamper(token)) });
    expect(res.status === 401, answered(res));
  });
  await report.check(`${sys.protectedPath} answers 401 with another system's token`, async () => {
    let other = 'vrms';
    if (sysKey === 'vrms') {
      if (!(await isUp(ctx, '/vmms/health'))) return 'VMMS is not on the stack, so there is no other system token to try';
      other = 'vmms';
    }
    const foreign = await accessToken(ctx, other, 'multi.lead');
    const res = await http(protectedUrl, { headers: bearer(foreign) });
    expect(res.status === 401, answered(res));
  });

  if (sysKey === 'vmms') await vmmsExtras(ctx, report, token);
  if (sysKey === 'bms') await bmsExtras(ctx, report);

  // Last, because logout ends the account's whole web session
  if (login && token) {
    const oldCookie = `${login.rtName}=${login.jar.get(login.rtName)}`;
    let loggedOutAt = 0;
    const out = await report.check(`${sys.prefix}/session/logout answers 204`, async () => {
      const res = await http(`${ctx.api}${sys.prefix}/session/logout`, {
        method: 'POST',
        headers: jsonPost(login.webOrigin),
        body: '{}',
        jar: login.jar,
      });
      loggedOutAt = Date.now();
      forgetLogin(ctx, sys.account);
      expect(res.status === 204 || res.status === 200, answered(res));
    });
    if (out) {
      await report.check('after logout, refresh with the old cookie answers 401', async () => {
        const res = await refresh(ctx, login, oldCookie);
        expect(res.status === 401, answered(res));
      });
      await report.check('after logout, the old access token is refused with SESSION_ENDED within 31 s', async () => {
        report.note('waiting for the session check (up to 31 s)...');
        for (;;) {
          const res = await http(protectedUrl, { headers: bearer(token) });
          const waited = Date.now() - loggedOutAt;
          if (res.status === 401) {
            expect(res.json?.code === 'SESSION_ENDED', `${answered(res)}, expected SESSION_ENDED`);
            expect(waited <= SESSION_END_LIMIT_MS, `refused only after ${Math.round(waited / 1000)} s`);
            report.note(`refused after ${Math.round(waited / 1000)} s`);
            return;
          }
          expect(res.status === 200, answered(res));
          expect(waited <= SESSION_END_LIMIT_MS, `still accepted ${Math.round(waited / 1000)} s after logout`);
          await new Promise((r) => setTimeout(r, 2_000));
        }
      });
    }
  }
}

async function vmmsExtras(ctx, report, token) {
  await report.check('vmms.mech@ opening VMMS on the web ends at the portal with APP_NOT_ALLOWED&system=VMMS', () =>
    expectNotAllowed(ctx, 'vmms', 'vmms.mech'),
  );
  await report.check('vmms.mech@ signs in on the phone app (vmms-mobile) and opens /vmms/maintenance-schedules', async () => {
    const account = ctx.accounts['vmms.mech'];
    const res = await http(`${ctx.api}/auth/mobile/login`, {
      method: 'POST',
      headers: jsonPost(null),
      body: JSON.stringify({ email: account.email, password: account.password, clientId: 'vmms-mobile', deviceName: 'check-system' }),
    });
    expect(res.status === 200 && res.json?.accessToken, `/auth/mobile/login ${answered(res)}`);
    const { accessToken: mobile, refreshToken } = res.json;
    try {
      const open = await http(`${ctx.api}/vmms/maintenance-schedules`, { headers: bearer(mobile) });
      expect(open.status === 200, `/vmms/maintenance-schedules ${answered(open)}`);
    } finally {
      // Ends the phone session again, so runs don't pile up sessions
      await http(`${ctx.api}/auth/logout`, {
        method: 'POST',
        headers: jsonPost(null),
        body: JSON.stringify({ refreshToken, clientId: 'vmms-mobile' }),
      }).catch(() => {});
    }
  });
  await report.check('/vmms/analytics/health answers 200', async () => {
    const res = await http(`${ctx.api}/vmms/analytics/health`);
    expect(res.status === 200, answered(res));
  });
  await report.check('/vmms/analytics/overview takes the VMMS user token', async () => {
    if (!token) return 'no VMMS token (the sign in failed above)';
    const res = await http(`${ctx.api}/vmms/analytics/overview`, { headers: bearer(token) });
    expect(res.status === 200, answered(res));
  });
  await report.check("/vmms/analytics/overview answers 401 with another system's token", async () => {
    const foreign = await accessToken(ctx, 'vrms', 'multi.lead');
    const res = await http(`${ctx.api}/vmms/analytics/overview`, { headers: bearer(foreign) });
    expect(res.status === 401, answered(res));
  });
}

async function bmsExtras(ctx, report) {
  await report.check('driver.ramon@ opening BMS on the web ends at the portal with APP_NOT_ALLOWED&system=BMS', () =>
    expectNotAllowed(ctx, 'bms', 'driver.ramon'),
  );
  await report.check('a 5 MB body to POST /bms/booking passes the BMS gateway and answers 400 from validation', async () => {
    const token = await accessToken(ctx, 'bms', 'bms.cs');
    const body = JSON.stringify({ checkSystemPadding: 'x'.repeat(BIG_BODY_BYTES) });
    const res = await http(`${ctx.api}/bms/booking`, {
      method: 'POST',
      headers: { ...jsonPost(null), ...bearer(token) },
      body,
      timeoutMs: 60_000,
    });
    if (res.status === 413) throw new Failure('413: a body limit below 10 MB (the BMS gateway or booking)');
    expect(res.status === 400, answered(res));
  });
}

/** Every plate number in a JSON answer, from active, not deleted vehicles, wherever the list sits. */
export function plates(json) {
  const found = new Set();
  const visit = (value) => {
    if (Array.isArray(value)) value.forEach(visit);
    else if (value && typeof value === 'object') {
      if (typeof value.plateNumber === 'string') {
        if (value.isActive !== false && !value.deletedAt) found.add(value.plateNumber);
        return;
      }
      Object.values(value).forEach(visit);
    }
  };
  visit(json);
  return found;
}

async function fleetGroup(ctx, report, sysKey) {
  report.start('fleet', 'Fleet API (VMMS serving, BMS reading)');
  const vmmsUp = await isUp(ctx, '/vmms/health');
  const bmsUp = await isUp(ctx, '/bms/health');
  if (!vmmsUp) {
    report.fail('VMMS is on the stack', '/vmms/health does not answer 200; BMS reads its trucks from VMMS');
    return;
  }
  for (const path of ['/vmms/fleet/vehicles', '/vmms/fleet/vehicles/00000000-0000-4000-8000-000000000000', '/vmms/fleet/garages']) {
    await report.check(`${path} answers 401 with no token`, async () => {
      const res = await http(`${ctx.api}${path}`);
      expect(res.status === 401, answered(res));
    });
  }
  let vmmsToken;
  await report.check('/vmms/fleet/vehicles answers 403 WRONG_TOKEN_USE with a user token', async () => {
    vmmsToken = await accessToken(ctx, 'vmms', 'vmms.ops');
    const res = await http(`${ctx.api}/vmms/fleet/vehicles`, { headers: bearer(vmmsToken) });
    expect(res.status === 403 && res.json?.code === 'WRONG_TOKEN_USE', answered(res));
  });
  await report.check('BMS lists the same plate numbers as VMMS (fleet.read end to end)', async () => {
    if (!bmsUp) {
      if (sysKey === 'bms') throw new Failure('/bms/health does not answer 200');
      return 'BMS is not on the stack yet, so nothing reads the fleet API';
    }
    vmmsToken ??= await accessToken(ctx, 'vmms', 'vmms.ops');
    const fromVmms = await http(`${ctx.api}/vmms/vehicles`, { headers: bearer(vmmsToken) });
    expect(fromVmms.status === 200, `/vmms/vehicles ${answered(fromVmms)}`);
    const bmsToken = await accessToken(ctx, 'bms', 'bms.ops');
    const fromBms = await http(`${ctx.api}/bms/config/vehicles`, { headers: bearer(bmsToken) });
    expect(fromBms.status === 200, `/bms/config/vehicles ${answered(fromBms)}`);
    const want = plates(fromVmms.json);
    const got = plates(fromBms.json);
    expect(want.size > 0, 'VMMS lists no vehicles; seed VMMS first');
    const missing = [...want].filter((p) => !got.has(p));
    const extra = [...got].filter((p) => !want.has(p));
    expect(
      missing.length === 0 && extra.length === 0,
      `missing in BMS: ${missing.slice(0, 5).join(', ') || 'none'}; only in BMS: ${extra.slice(0, 5).join(', ') || 'none'}`,
    );
    report.note(`${want.size} plates match`);
  });
}

function staticGroup(report, sysKey) {
  report.start('static', `${SYSTEMS[sysKey].code} leftovers scan (repos on disk)`);
  for (const repo of SYSTEMS[sysKey].repos) {
    const dir = join(ROOT, repo);
    if (!existsSync(dir)) {
      report.fail(repo, `not cloned, so not scanned (run: sh scripts/clone-all.sh ${sysKey})`);
      continue;
    }
    const { files, hits, allowed } = scanRepo(dir);
    for (const a of allowed) console.log(`allow ${a.file}:${a.line}  ${a.rule} (${a.reason})`);
    if (hits.length === 0) {
      report.ok(`${repo}: no leftovers in ${files} files`);
      continue;
    }
    for (const h of hits) report.fail(`${h.file}:${h.line}`, h.rule);
  }
}

// ---------------------------------------------------------------- main

function usage(message) {
  if (message) console.error(message);
  console.error(
    'Usage: node scripts/check-system.mjs <vrms|vmms|bms> [--static-only | --live-only] [--login] [--fleet]\n' +
      '       [--api <url>] [--portal <url>] [--accounts <file>]',
  );
  process.exit(message ? 1 : 0);
}

export function parseArgs(argv) {
  const opts = { api: 'http://localhost:3000', portal: 'http://localhost:8000', accounts: null, groups: new Set() };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const value = () => {
      const v = argv[++i];
      if (!v || v.startsWith('--')) throw new Error(`${arg} needs a value`);
      return v;
    };
    if (arg in SYSTEMS) opts.system = arg;
    else if (arg === '--api') opts.api = value();
    else if (arg === '--portal') opts.portal = value();
    else if (arg === '--accounts') opts.accounts = value();
    else if (arg === '--static-only') opts.staticOnly = true;
    else if (arg === '--live-only') opts.liveOnly = true;
    else if (arg === '--login') opts.groups.add('login');
    else if (arg === '--fleet') opts.groups.add('fleet');
    else if (arg === '--help' || arg === '-h') opts.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (opts.staticOnly && opts.liveOnly) throw new Error('--static-only and --live-only exclude each other');
  opts.api = opts.api.replace(/\/+$/, '');
  opts.portal = opts.portal.replace(/\/+$/, '');
  return opts;
}

async function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (error) {
    usage(error.message);
  }
  if (opts.help) usage();
  if (!opts.system) usage('Name the system to check: vrms, vmms or bms.');

  const accounts = { ...DEFAULT_ACCOUNTS };
  if (opts.accounts) {
    const extra = JSON.parse(readFileSync(resolve(opts.accounts), 'utf8'));
    for (const [key, value] of Object.entries(extra)) accounts[key] = { ...accounts[key], ...value };
  }
  const ctx = { api: opts.api, portalOrigin: new URL(opts.portal).origin, accounts, sso: new Map() };
  const report = new Report();
  const live = !opts.staticOnly;
  const wants = (group) => opts.groups.size === 0 || opts.groups.has(group);

  if (live) {
    let up = false;
    try {
      up = (await http(`${ctx.api}/health`, { timeoutMs: 5_000 })).status === 200;
    } catch {
      up = false;
    }
    if (!up) {
      console.error(`The gateway at ${ctx.api} doesn't answer. Start the stack first: sh scripts/start.sh ${opts.system}`);
      process.exit(2);
    }
    if (wants('login')) await loginGroup(ctx, report, opts.system);
    if (wants('fleet') && opts.system !== 'vrms') await fleetGroup(ctx, report, opts.system);
  }
  if (!opts.liveOnly && opts.groups.size === 0) staticGroup(report, opts.system);

  report.summary();
  process.exit(report.failed ? 1 : 0);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
