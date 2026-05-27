# Этап 1: Сборка Admin Panel
FROM node:20-alpine AS build-admin
ARG VITE_WEBHOOK_DOMAIN
ENV VITE_WEBHOOK_DOMAIN=$VITE_WEBHOOK_DOMAIN
WORKDIR /app/admin
COPY admin/package*.json ./
RUN npm install
COPY admin/ ./
RUN npm run build

# Этап 2: Сборка Telegram Mini App (TMA)
FROM node:20-alpine AS build-tma
WORKDIR /app/tma
COPY tma/package*.json ./
RUN npm install
COPY tma/ ./
RUN npm run build

# Этап 3: Финальный образ Nginx
FROM nginx:alpine AS final
# Размещаем Admin Panel в корне
COPY --from=build-admin /app/admin/dist /usr/share/nginx/html
# Размещаем TMA по вложенному пути /tma
COPY --from=build-tma  /app/tma/dist  /usr/share/nginx/html/tma
