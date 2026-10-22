FROM nginx:stable-alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY conf.d/ /etc/nginx/conf.d/

COPY snippets/ /etc/nginx/snippets/

RUN nginx -t
