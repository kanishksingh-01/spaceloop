FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install || true
COPY frontend/ ./
RUN npm run build || true
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
