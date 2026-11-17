# The suite gateway (spec 0008). One image for every environment, run from settings alone:
# see README.md for the settings and how to add a route.
FROM nginx:1.30-alpine

# Writes NGINX_LOCAL_RESOLVERS from /etc/resolv.conf at start (Docker's DNS locally, Azure's when hosted)
ENV NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1

# Our templates replace the stock server; generated/ holds the CORS origin map the start check writes
RUN rm -f /etc/nginx/conf.d/default.conf && mkdir -p /etc/nginx/generated

COPY nginx.conf /etc/nginx/nginx.conf
COPY templates/ /etc/nginx/templates/
# The Sentry tunnel's envelope check (VRMS spec 0025), imported by default.conf.template
COPY njs/ /etc/nginx/njs/
COPY docker-entrypoint.d/05-check-env.sh /docker-entrypoint.d/05-check-env.sh
# The image silently skips a start script that isn't executable
RUN chmod +x /docker-entrypoint.d/05-check-env.sh

EXPOSE 3000
