FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json /app/
RUN npm ci

COPY frontend /app

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM nginx:alpine

COPY frontend/nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# envsubst replaces ${API_KEY} in the template at startup, then launches Nginx.
# Only substitute API_KEY — leave Nginx's own $variables untouched.
CMD ["/bin/sh", "-c", "envsubst '${API_KEY}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
