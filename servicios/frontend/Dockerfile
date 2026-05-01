# Stage 1: build React app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: serve with nginx
FROM nginx:1.25-alpine

RUN addgroup -S shieldscan && adduser -S shieldscan -G shieldscan

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R shieldscan:shieldscan /usr/share/nginx/html && \
    chown -R shieldscan:shieldscan /var/cache/nginx && \
    chown -R shieldscan:shieldscan /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown shieldscan:shieldscan /var/run/nginx.pid

USER shieldscan

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
