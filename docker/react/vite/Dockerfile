FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci
COPY . .

# Build ra thư mục dist
RUN npm run build


FROM nginxinc/nginx-unprivileged:alpine AS production

# Copy các file static vào thư mục web của Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# (Tùy chọn) Copy file cấu hình Nginx tùy chỉnh (nếu bạn có dùng SPA routing)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Image này mặc định chạy ở cổng 8080 (vì cổng < 1024 yêu cầu root)
EXPOSE 8080