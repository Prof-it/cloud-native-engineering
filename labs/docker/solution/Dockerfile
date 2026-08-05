FROM nginx:1.27-alpine
COPY app/index.html /usr/share/nginx/html/index.html
RUN addgroup -S app && adduser -S -G app app \
  && chown -R app:app /usr/share/nginx/html
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
