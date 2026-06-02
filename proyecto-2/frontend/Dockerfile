# Servidor de desarrollo Vite (TAAM). Produccion: build estatico embebido en la API (futuro).
FROM node:22-alpine

WORKDIR /app

RUN npm install -g pnpm@11.1.1

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 5174

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
