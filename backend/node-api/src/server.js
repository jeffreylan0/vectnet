import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import 'dotenv/config';

import recognizeRoutes from './routes/recognize.js';

const fastify = Fastify({
  logger: true,
});

// --- Middleware & Plugins ---
// Security headers
fastify.register(helmet);

// CORS
fastify.register(cors, {
  origin: [process.env.FRONTEND_URL, 'http://localhost:5000'],
  methods: ['POST'],
});

// Rate Limiting
fastify.register(rateLimit, {
  max: 100,
  timeWindow: '15 minutes',
});

// --- Routes ---
fastify.register(recognizeRoutes, { prefix: '/api/shapes' });

// --- Start Server ---
const start = async () => {
  try {
    await fastify.listen({ port: process.env.PORT || 3001, host: '0.0.0.0' });
    fastify.log.info(`Server listening on ${fastify.server.address().port}`);
  } catch (err) {
    fastify.log.error(err);
    process.exit(1);
  }
};

start();
