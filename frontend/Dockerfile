# Stage 1: Base
# Node 24.13.0 (Krypton LTS) as specified in .nvmrc
FROM node:24.13.0-alpine AS base
WORKDIR /app

# Enable corepack for fast, official pnpm management
RUN corepack enable && corepack prepare pnpm@latest --activate

# Stage 2: Dependencies
FROM base AS deps
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Stage 3: Builder
FROM deps AS builder
COPY frontend/ .
# Build Arguments
ARG VITE_API_URL
ARG VITE_AZURE_CLIENT_ID
ARG VITE_AZURE_TENANT_ID
ARG VITE_AZURE_AUTHORITY
ARG VITE_BYPASS_AUTH

# Set Environment Variables for Build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_AZURE_CLIENT_ID=$VITE_AZURE_CLIENT_ID
ENV VITE_AZURE_TENANT_ID=$VITE_AZURE_TENANT_ID
ENV VITE_AZURE_AUTHORITY=$VITE_AZURE_AUTHORITY
ENV VITE_BYPASS_AUTH=$VITE_BYPASS_AUTH

RUN pnpm run build

# Stage 4: Test / E2E Runner (Playwright)
# Using Playwright's jammy base for best compatibility with E2E environments
FROM mcr.microsoft.com/playwright:v1.58.0-jammy AS test
WORKDIR /app
RUN npm install -g pnpm
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ .
ENV VITE_BYPASS_AUTH=$VITE_BYPASS_AUTH
CMD ["pnpm", "test"]

# Stage 5: Production
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
