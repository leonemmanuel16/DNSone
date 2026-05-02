# =============================================================================
# DNS One — Frontend Dockerfile (desarrollo: dev mode con hot reload)
# Para producción: hacer multi-stage build con `next build` y `next start`.
# =============================================================================
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
