import { recognizeShape } from '../controllers/shapeController.js';

async function routes(fastify, options) {
  fastify.post('/recognize', recognizeShape);
}

export default routes;
