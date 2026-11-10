// A stand in upstream for the gateway tests (spec 0008). Answers with what it received, as JSON.
//   ?delay=<ms>   wait before answering (the timeout check)
//   ?status=<n>   answer with that status and this same JSON body (the passthrough check)
//   ?cors=1       send its own CORS, Vary, X-Request-Id and HSTS headers (the gateway must hide them)
// A path ending in /session/refresh also sets a cookie. Each request is logged as "METHOD URL", so the
// script can prove a request never reached an upstream.
import http from 'node:http';

const service = process.env.SERVICE ?? 'stub';
const port = Number(process.env.PORT ?? 3000);

http
  .createServer((req, res) => {
    let bytes = 0;
    req.on('data', (chunk) => {
      bytes += chunk.length;
    });
    req.on('end', () => {
      console.log(`${req.method} ${req.url}`);
      const url = new URL(req.url, 'http://stub');
      const headers = { 'Content-Type': 'application/json' };
      if (url.searchParams.get('cors') === '1') {
        Object.assign(headers, {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET',
          'Access-Control-Allow-Headers': 'X-Anything',
          'Access-Control-Expose-Headers': 'X-Secret',
          'Access-Control-Max-Age': '99999',
          Vary: 'Accept-Encoding',
          'X-Request-Id': 'from-upstream',
          'Strict-Transport-Security': 'max-age=999',
        });
      }
      if (url.pathname.endsWith('/session/refresh')) {
        headers['Set-Cookie'] = 'stub_rt=1; Path=/; HttpOnly';
      }
      const send = () => {
        res.writeHead(Number(url.searchParams.get('status') ?? 200), headers);
        res.end(JSON.stringify({ service, method: req.method, url: req.url, headers: req.headers, bytes }));
      };
      const delay = Number(url.searchParams.get('delay') ?? 0);
      if (delay > 0) setTimeout(send, delay);
      else send();
    });
  })
  .listen(port, () => console.log(`stub ${service} listening on ${port}`));
