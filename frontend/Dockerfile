# Use official Node 20 slim image
FROM node:20-slim

# Install pnpm globally
RUN npm install -g pnpm

# Set working directory
WORKDIR /app

# Copy package files for layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install

# Copy the rest of the frontend source code
COPY . .

# Expose the Vite development port
EXPOSE 5173

# Start the Vite server, binding to 0.0.0.0 so it is accessible outside the container
CMD ["pnpm", "run", "dev", "--host", "0.0.0.0"]