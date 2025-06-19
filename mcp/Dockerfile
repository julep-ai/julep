# Multi-stage build for Julep Unified MCP Server
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY src/ ./src/
COPY build.sh ./

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install production dependencies only
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy built application
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Switch to non-root user
USER nodejs

# Expose port for HTTP transport
EXPOSE 3000

# Default to HTTP transport for service mode
ENV TRANSPORT=http
ENV PORT=3000

# Entry point
ENTRYPOINT ["node", "dist/index.js"]

# Default command (can be overridden)
CMD ["--transport", "http", "--port", "3000"]