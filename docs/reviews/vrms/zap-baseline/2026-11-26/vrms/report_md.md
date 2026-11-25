# ZAP Scanning Report

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 1 |
| Low | 2 |
| Informational | 5 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Low | Warning |  | ZAP warnings logged - see the zap.log file for details | 10    |
| Info | Informational | https://staging-api.welinc.app | Percentage of endpoints with content type application/json | 55 % |
| Info | Informational | https://staging-api.welinc.app | Percentage of endpoints with content type text/html | 22 % |
| Info | Informational | https://staging-api.welinc.app | Percentage of endpoints with method GET | 33 % |
| Info | Informational | https://staging-api.welinc.app | Percentage of endpoints with method OPTIONS | 22 % |
| Info | Informational | https://staging-api.welinc.app | Percentage of endpoints with method POST | 44 % |
| Info | Informational | https://staging-api.welinc.app | Count of total endpoints | 9    |
| Info | Informational | https://staging-portal.welinc.app | Percentage of endpoints with content type application/octet-stream | 16 % |
| Info | Informational | https://staging-portal.welinc.app | Percentage of endpoints with content type font/woff2 | 16 % |
| Info | Informational | https://staging-portal.welinc.app | Percentage of endpoints with content type image/svg+xml | 16 % |
| Info | Informational | https://staging-portal.welinc.app | Percentage of endpoints with content type text/css | 16 % |
| Info | Informational | https://staging-portal.welinc.app | Percentage of endpoints with content type text/html | 16 % |
| Info | Informational | https://staging-portal.welinc.app | Percentage of endpoints with content type text/javascript | 16 % |
| Info | Informational | https://staging-portal.welinc.app | Percentage of endpoints with method GET | 100 % |
| Info | Informational | https://staging-portal.welinc.app | Count of total endpoints | 6    |
| Info | Informational | https://staging-vrms.welinc.app | Percentage of responses with status code 2xx | 83 % |
| Info | Informational | https://staging-vrms.welinc.app | Percentage of responses with status code 4xx | 16 % |
| Info | Informational | https://staging-vrms.welinc.app | Percentage of endpoints with content type text/css | 14 % |
| Info | Informational | https://staging-vrms.welinc.app | Percentage of endpoints with content type text/html | 57 % |
| Info | Informational | https://staging-vrms.welinc.app | Percentage of endpoints with content type text/javascript | 28 % |
| Info | Informational | https://staging-vrms.welinc.app | Percentage of endpoints with method GET | 100 % |
| Info | Informational | https://staging-vrms.welinc.app | Count of total endpoints | 7    |
| Info | Informational | https://staging-vrms.welinc.app | Percentage of slow responses | 50 % |







## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| CSP: style-src unsafe-inline | Medium | 5 |
| Cross-Origin-Embedder-Policy Header Missing or Invalid | Low | 3 |
| Timestamp Disclosure - Unix | Low | Systemic |
| Information Disclosure - Information in Browser sessionStorage | Informational | 1 |
| Information Disclosure - Suspicious Comments | Informational | 1 |
| Modern Web Application | Informational | 5 |
| Re-examine Cache-control Directives | Informational | 3 |
| Storable and Cacheable Content | Informational | Systemic |




## Alert Detail



### [ CSP: style-src unsafe-inline ](https://www.zaproxy.org/docs/alerts/10055/)



##### Medium (High)

### Description

Content Security Policy (CSP) is an added layer of security that helps to detect and mitigate certain types of attacks. Including (but not limited to) Cross Site Scripting (XSS), and data injection attacks. These attacks are used for everything from data theft to site defacement or distribution of malware. CSP provides a set of standard HTTP headers that allow website owners to declare approved sources of content that browsers should be allowed to load on that page — covered types are JavaScript, CSS, HTML frames, fonts, images and embeddable objects such as Java applets, ActiveX, audio and video files.

* URL: https://staging-vrms.welinc.app
  * Node Name: `https://staging-vrms.welinc.app`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `default-src 'self'; connect-src 'self' https://*.welinc.app; img-src 'self' data: blob: https://*.welinc.app https://*.blob.core.windows.net; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
  * Other Info: `style-src includes unsafe-inline.`
* URL: https://staging-vrms.welinc.app/
  * Node Name: `https://staging-vrms.welinc.app/`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `default-src 'self'; connect-src 'self' https://*.welinc.app; img-src 'self' data: blob: https://*.welinc.app https://*.blob.core.windows.net; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
  * Other Info: `style-src includes unsafe-inline.`
* URL: https://staging-vrms.welinc.app/favicon.ico
  * Node Name: `https://staging-vrms.welinc.app/favicon.ico`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `default-src 'self'; connect-src 'self' https://*.welinc.app; img-src 'self' data: blob: https://*.welinc.app https://*.blob.core.windows.net; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
  * Other Info: `style-src includes unsafe-inline.`
* URL: https://staging-vrms.welinc.app/robots.txt
  * Node Name: `https://staging-vrms.welinc.app/robots.txt`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `default-src 'self'; connect-src 'self' https://*.welinc.app; img-src 'self' data: blob: https://*.welinc.app https://*.blob.core.windows.net; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
  * Other Info: `style-src includes unsafe-inline.`
* URL: https://staging-vrms.welinc.app/sitemap.xml
  * Node Name: `https://staging-vrms.welinc.app/sitemap.xml`
  * Method: `GET`
  * Parameter: `Content-Security-Policy`
  * Attack: ``
  * Evidence: `default-src 'self'; connect-src 'self' https://*.welinc.app; img-src 'self' data: blob: https://*.welinc.app https://*.blob.core.windows.net; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'`
  * Other Info: `style-src includes unsafe-inline.`


Instances: 5

### Solution

Ensure that your web server, application server, load balancer, etc. is properly configured to set the Content-Security-Policy header.

### Reference


* [ https://www.w3.org/TR/CSP/ ](https://www.w3.org/TR/CSP/)
* [ https://caniuse.com/#search=content+security+policy ](https://caniuse.com/#search=content+security+policy)
* [ https://content-security-policy.com/ ](https://content-security-policy.com/)
* [ https://github.com/HtmlUnit/htmlunit-csp ](https://github.com/HtmlUnit/htmlunit-csp)
* [ https://web.dev/articles/csp#resource-options ](https://web.dev/articles/csp#resource-options)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 15

#### Source ID: 3

### [ Cross-Origin-Embedder-Policy Header Missing or Invalid ](https://www.zaproxy.org/docs/alerts/90004/)



##### Low (Medium)

### Description

Cross-Origin-Embedder-Policy header is a response header that prevents a document from loading any cross-origin resources that don't explicitly grant the document permission (using CORP or CORS).

* URL: https://staging-vrms.welinc.app
  * Node Name: `https://staging-vrms.welinc.app`
  * Method: `GET`
  * Parameter: `Cross-Origin-Embedder-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/
  * Node Name: `https://staging-vrms.welinc.app/`
  * Method: `GET`
  * Parameter: `Cross-Origin-Embedder-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/sitemap.xml
  * Node Name: `https://staging-vrms.welinc.app/sitemap.xml`
  * Method: `GET`
  * Parameter: `Cross-Origin-Embedder-Policy`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``


Instances: 3

### Solution

Ensure that the application/web server sets the Cross-Origin-Embedder-Policy header appropriately, and that it sets the Cross-Origin-Embedder-Policy header to 'require-corp' for documents.
If possible, ensure that the end user uses a standards-compliant and modern web browser that supports the Cross-Origin-Embedder-Policy header (https://caniuse.com/mdn-http_headers_cross-origin-embedder-policy).

### Reference


* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 14

#### Source ID: 3

### [ Timestamp Disclosure - Unix ](https://www.zaproxy.org/docs/alerts/10096/)



##### Low (Low)

### Description

A timestamp was disclosed by the application/web server. - Unix

* URL: https://staging-vrms.welinc.app/assets/index-DAomlpY5.js
  * Node Name: `https://staging-vrms.welinc.app/assets/index-DAomlpY5.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `1502002290`
  * Other Info: `1502002290, which evaluates to: 2017-08-06 06:51:30.`
* URL: https://staging-vrms.welinc.app/assets/index-DAomlpY5.js
  * Node Name: `https://staging-vrms.welinc.app/assets/index-DAomlpY5.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `1770035416`
  * Other Info: `1770035416, which evaluates to: 2026-02-02 12:30:16.`
* URL: https://staging-vrms.welinc.app/assets/index-DAomlpY5.js
  * Node Name: `https://staging-vrms.welinc.app/assets/index-DAomlpY5.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `1804603682`
  * Other Info: `1804603682, which evaluates to: 2027-03-09 14:48:02.`
* URL: https://staging-vrms.welinc.app/assets/index-DAomlpY5.js
  * Node Name: `https://staging-vrms.welinc.app/assets/index-DAomlpY5.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `1958414417`
  * Other Info: `1958414417, which evaluates to: 2032-01-22 20:00:17.`
* URL: https://staging-vrms.welinc.app/assets/index-DAomlpY5.js
  * Node Name: `https://staging-vrms.welinc.app/assets/index-DAomlpY5.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `1990404162`
  * Other Info: `1990404162, which evaluates to: 2033-01-27 02:02:42.`

Instances: Systemic


### Solution

Manually confirm that the timestamp data is not sensitive, and that the data cannot be aggregated to disclose exploitable patterns.

### Reference


* [ https://cwe.mitre.org/data/definitions/200.html ](https://cwe.mitre.org/data/definitions/200.html)


#### CWE Id: [ 497 ](https://cwe.mitre.org/data/definitions/497.html)


#### WASC Id: 13

#### Source ID: 3

### [ Information Disclosure - Information in Browser sessionStorage ](https://www.zaproxy.org/docs/alerts/120000/)



##### Informational (High)

### Description

Information was stored in browser sessionStorage.
This is not unusual or necessarily unsafe - this informational alert has been raised to help you get a better understanding of what this app is doing. For more details see the Client tabs - this information was set directly in the browser and will therefore not necessarily appear in this form in any HTTP(S) messages.

* URL: https://staging-vrms.welinc.app/
  * Node Name: `https://staging-vrms.welinc.app/`
  * Method: `GET`
  * Parameter: `vrms_boot_attempt`
  * Attack: ``
  * Evidence: ``
  * Other Info: `The following data (key=value) was set: vrms_boot_attempt=1795624924531
Note that this alert will only be raised once for each URL + key.`


Instances: 1

### Solution

This is an informational alert and no action is necessary. 

### Reference



#### CWE Id: [ 359 ](https://cwe.mitre.org/data/definitions/359.html)


#### WASC Id: 13

#### Source ID: 3

### [ Information Disclosure - Suspicious Comments ](https://www.zaproxy.org/docs/alerts/10027/)



##### Informational (Medium)

### Description

The response appears to contain suspicious comments which may help an attacker.

* URL: https://staging-vrms.welinc.app/assets/index-DAomlpY5.js
  * Node Name: `https://staging-vrms.welinc.app/assets/index-DAomlpY5.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `eldContext,field:``,query:{},parse:this.parse`
  * Other Info: `The following pattern was used: \bQUERY\b and was detected in likely comment: "//,``).split(`/`);m=`/`+p.replace(/^\//,``).split(`/`).slice(e.length).join(`/`)}let h=n&&n.state.matches.length?n.state.matches", see evidence field for the suspicious comment/snippet.`


Instances: 1

### Solution

Remove all comments that return information that may help an attacker and fix any underlying problems they refer to.

### Reference



#### CWE Id: [ 615 ](https://cwe.mitre.org/data/definitions/615.html)


#### WASC Id: 13

#### Source ID: 3

### [ Modern Web Application ](https://www.zaproxy.org/docs/alerts/10109/)



##### Informational (Medium)

### Description

The application appears to be a modern web application. If you need to explore it automatically then the Client Spider may well be more effective than the standard one.

* URL: https://staging-vrms.welinc.app
  * Node Name: `https://staging-vrms.welinc.app`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-DAomlpY5.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://staging-vrms.welinc.app/
  * Node Name: `https://staging-vrms.welinc.app/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-DAomlpY5.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://staging-vrms.welinc.app/favicon.ico
  * Node Name: `https://staging-vrms.welinc.app/favicon.ico`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-DAomlpY5.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://staging-vrms.welinc.app/robots.txt
  * Node Name: `https://staging-vrms.welinc.app/robots.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-DAomlpY5.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://staging-vrms.welinc.app/sitemap.xml
  * Node Name: `https://staging-vrms.welinc.app/sitemap.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-DAomlpY5.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`


Instances: 5

### Solution

This is an informational alert and so no changes are required.

### Reference




#### Source ID: 3

### [ Re-examine Cache-control Directives ](https://www.zaproxy.org/docs/alerts/10015/)



##### Informational (Low)

### Description

The cache-control header has not been set properly or is missing, allowing the browser and proxies to cache content. For static assets like css, js, or image files this might be intended, however, the resources should be reviewed to ensure that no sensitive content will be cached.

* URL: https://staging-vrms.welinc.app
  * Node Name: `https://staging-vrms.welinc.app`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, must-revalidate, max-age=30`
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/
  * Node Name: `https://staging-vrms.welinc.app/`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, must-revalidate, max-age=30`
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/sitemap.xml
  * Node Name: `https://staging-vrms.welinc.app/sitemap.xml`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, must-revalidate, max-age=30`
  * Other Info: ``


Instances: 3

### Solution

For secure content, ensure the cache-control HTTP header is set with "no-cache, no-store, must-revalidate". If an asset should be cached consider setting the directives "public, max-age, immutable".

### Reference


* [ https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#web-content-caching ](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#web-content-caching)
* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
* [ https://grayduck.mn/2021/09/13/cache-control-recommendations/ ](https://grayduck.mn/2021/09/13/cache-control-recommendations/)


#### CWE Id: [ 525 ](https://cwe.mitre.org/data/definitions/525.html)


#### WASC Id: 13

#### Source ID: 3

### [ Storable and Cacheable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are storable by caching components such as proxy servers, and may be retrieved directly from the cache, rather than from the origin server by the caching servers, in response to similar requests from other users. If the response data is sensitive, personal or user-specific, this may result in sensitive information being leaked. In some cases, this may even result in a user gaining complete control of the session of another user, depending on the configuration of the caching components in use in their environment. This is primarily an issue where "shared" caching servers such as "proxy" caches are configured on the local network. This configuration is typically found in corporate or educational environments, for instance.

* URL: https://staging-vrms.welinc.app
  * Node Name: `https://staging-vrms.welinc.app`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=30`
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/assets/index-2uhZSA2X.css
  * Node Name: `https://staging-vrms.welinc.app/assets/index-2uhZSA2X.css`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=30`
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/assets/rolldown-runtime-DYkMjGo5.js
  * Node Name: `https://staging-vrms.welinc.app/assets/rolldown-runtime-DYkMjGo5.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=30`
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/robots.txt
  * Node Name: `https://staging-vrms.welinc.app/robots.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=30`
  * Other Info: ``
* URL: https://staging-vrms.welinc.app/sitemap.xml
  * Node Name: `https://staging-vrms.welinc.app/sitemap.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `max-age=30`
  * Other Info: ``

Instances: Systemic


### Solution

Validate that the response does not contain sensitive, personal or user-specific information. If it does, consider the use of the following HTTP response headers, to limit, or prevent the content being stored and retrieved from the cache by another user:
Cache-Control: no-cache, no-store, must-revalidate, private
Pragma: no-cache
Expires: 0
This configuration directs both HTTP 1.0 and HTTP 1.1 compliant caching servers to not store the response, and to not retrieve the response (without validation) from the cache, in response to a similar request.

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3


