// VRMS spec 0025, AC-5: the Sentry tunnel's envelope check. Sentry files an envelope under the DSN
// in its first line (its header) and ignores the project id in the address it receives, so the
// gateway itself makes sure each route only ever relays its own project's reports.
//
// Runs as `js_content tunnel.check` in each public /monitoring/* location, after the method checks
// and the rate limit. Reads the route's own DSN parts from the nginx variables 05-check-env.sh
// writes ($tunnel_key, $tunnel_host, $tunnel_project, $tunnel_target), never from the environment.
// Forwards with an internal redirect, so nginx proxies the body it already read, byte for byte.
// Logs nothing from the body.

// The one DSN pattern, the same literal as in 05-check-env.sh
const DSN = /^https:\/\/([0-9a-f]{32})@(o[0-9]+\.ingest(\.[a-z]{2})?\.sentry\.io)\/([1-9][0-9]*)$/;
const HEADER_LIMIT = 8192;

const REJECTED = JSON.stringify({
  statusCode: 403,
  message: 'Envelope DSN does not match this route',
  error: 'Forbidden',
  code: 'TUNNEL_REJECTED',
});
const TOO_LARGE = JSON.stringify({
  statusCode: 413,
  message: "Request body is over this route's limit",
  error: 'Payload Too Large',
  code: 'PAYLOAD_TOO_LARGE',
});

/** The envelope header's `dsn`, or undefined when the body breaks any rule before the compare. */
function headerDsn(r, body) {
  // 1. A compressed body hides its header (the browser SDK sends plain text)
  const encoding = r.headersIn['Content-Encoding'];
  if (encoding !== undefined && encoding.trim().toLowerCase() !== 'identity') return undefined;

  // 2. The header line ends within the first 8 KB (a trailing \r is ignored)
  const newline = body.subarray(0, HEADER_LIMIT).indexOf(0x0a);
  if (newline < 0) return undefined;
  let line = body.subarray(0, newline).toString('utf8');
  if (line.endsWith('\r')) line = line.slice(0, -1);

  // 3. Exactly one "dsn" and no \u escape, so njs and Sentry can't each read a different DSN
  if (line.split('"dsn"').length !== 2 || line.indexOf('\\u') !== -1) return undefined;

  // 4. A JSON object whose dsn is a string
  let header;
  try {
    header = JSON.parse(line);
  } catch (e) {
    return undefined;
  }
  if (header === null || typeof header !== 'object' || Array.isArray(header)) return undefined;
  return typeof header.dsn === 'string' ? header.dsn : undefined;
}

function check(r) {
  let body;
  try {
    body = r.requestBuffer;
  } catch (e) {
    body = undefined;
  }
  // An empty body has no header line (njs hands it over as an empty value, not a Buffer)
  const length = Number(r.headersIn['Content-Length'] || 0);
  if (!body || body.length === 0) {
    // A body that has length but no buffer went to a temp file, which the 1 MB single buffer rules out
    if (length > 0 && (body === undefined || body === null)) {
      r.return(413, TOO_LARGE);
      return;
    }
    r.return(403, REJECTED);
    return;
  }
  if (typeof body === 'string') body = Buffer.from(body);

  // 5. The route's own DSN: same key, host and project id, exactly. The rebuilt string also refuses
  // anything the pattern's $ might let through (a trailing newline).
  const v = r.variables;
  const dsn = headerDsn(r, body);
  const parts = dsn === undefined ? null : DSN.exec(dsn);
  const own = `https://${v.tunnel_key}@${v.tunnel_host}/${v.tunnel_project}`;
  if (
    parts === null ||
    parts[1] !== v.tunnel_key ||
    parts[2] !== v.tunnel_host ||
    parts[4] !== v.tunnel_project ||
    dsn !== own
  ) {
    r.return(403, REJECTED);
    return;
  }

  r.internalRedirect(v.tunnel_target);
}

export default { check };
