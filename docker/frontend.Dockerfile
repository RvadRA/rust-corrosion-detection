# syntax=docker/dockerfile:1
# ------------------------------------------------------------------------------
# Стейдж 1: сборка React фронтенда
# ------------------------------------------------------------------------------
FROM node:20-alpine3.20 AS builder

WORKDIR /app

COPY src/frontend/package*.json ./
RUN npm ci --ignore-scripts

COPY src/frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Стейдж 2: раздача через Nginx
# ------------------------------------------------------------------------------
FROM nginx:1.27.0-alpine AS runtime

# Копируем конфигурацию Nginx
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Копируем собранные статические файлы
COPY --from=builder /app/dist /usr/share/nginx/html

# Настройка прав для работы от непривилегированного пользователя nginx
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /usr/share/nginx/html

USER nginx

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
