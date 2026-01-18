# Stage 1: Base
FROM node:23-alpine AS base
WORKDIR /app

# Stage 2: Dependencies
FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci

# Stage 3: Builder
FROM deps AS builder
COPY . .
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

RUN npm run build

# Stage 4: Test / E2E Runner (Playwright)
FROM mcr.microsoft.com/playwright:v1.57.0-jammy AS test
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci
COPY . .
ENV VITE_BYPASS_AUTH=true
CMD ["npx", "playwright", "test"]

# Stage 5: Production
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
