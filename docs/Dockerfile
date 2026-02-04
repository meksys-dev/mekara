# Development container with live reload
FROM node:20-alpine

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10.12.4 --activate

WORKDIR /app

# Copy package files first for better layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Source files will be mounted as a volume for live reload
# COPY . .

EXPOSE 4913

CMD ["pnpm", "start", "--host", "0.0.0.0"]
