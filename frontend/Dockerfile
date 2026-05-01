# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app

# Copy only the dependency manifests first so Docker can cache this layer.
# If package.json/package-lock.json haven't changed, npm ci is skipped on
# the next build — even if your source code changed.
COPY package.json package-lock.json ./
RUN npm ci

# Now copy the rest of the source and compile.
# Vite outputs to dist/ by default.
COPY . .
RUN npm run build

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
FROM nginx:alpine AS serve

# Pull only the compiled dist/ folder from Stage 1 — no Node, no source code,
# no node_modules makes it into this final image.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# nginx must run in the foreground so Docker knows the container is still alive.
CMD ["nginx", "-g", "daemon off;"]
