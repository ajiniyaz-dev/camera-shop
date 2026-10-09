FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
RUN addgroup -S catalog && adduser -S catalog -G catalog
COPY --from=builder /app/public ./public
COPY --from=builder --chown=catalog:catalog /app/.next/standalone ./
COPY --from=builder --chown=catalog:catalog /app/.next/static ./.next/static
USER catalog
EXPOSE 3000
CMD ["node", "server.js"]
