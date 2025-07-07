import sharp from 'sharp';
import axios from 'axios';
import FormData from 'form-data';
import pool from '../utils/dbClient.js'; // Updated import

export const recognizeShape = async (request, reply) => {
  try {
    // 1. Validate and get image data
    const { image: base64Image } = request.body;
    if (!base64Image || !base64Image.startsWith('data:image/png;base64,')) {
      return reply.code(400).send({ error: 'Invalid or missing image data.' });
    }

    // 2. Pre-process image with Sharp
    const imageBuffer = Buffer.from(
      base64Image.replace(/^data:image\/png;base64,/, ''),
      'base64'
    );
    
    const processedImageBuffer = await sharp(imageBuffer)
        .removeAlpha()
        .toFormat('png')
        .toBuffer();

    // 3. Call Python service to get feature vector
    const form = new FormData();
    form.append('file', processedImageBuffer, { filename: 'shape.png', contentType: 'image/png' });

    // Note: The environment variable was updated from PYTHON_SERVICE_URL to PYTHON_CV_URL
    const pythonServiceUrl = `${process.env.PYTHON_CV_URL}/process-image/`;
    
    const vectorResponse = await axios.post(pythonServiceUrl, form, {
      headers: form.getHeaders(),
    });

    const { feature_vector: featureVector } = vectorResponse.data;

    if (!featureVector || featureVector.length === 0) {
        return reply.code(400).send({ error: 'Could not extract features from shape.' });
    }

    // 4. Query database for the nearest neighbor
    const vectorString = `[${featureVector.join(',')}]`;
    const query = {
      text: `
        SELECT 
          id, 
          metadata,
          preview_image_url,
          canonical_vec <=> $1::vector AS similarity_distance
        FROM 
          shape_record
        ORDER BY 
          similarity_distance ASC
        LIMIT 1;
      `,
      values: [vectorString],
    };

    const { rows } = await pool.query(query);

    if (rows.length === 0) {
      return reply.code(404).send({ error: 'No matching shapes found in the registry.' });
    }

    const match = rows[0];
    const similarityScore = 1 - (match.similarity_distance / 2);

    // 5. Return the successful response
    return reply.code(200).send({
      matchedShapeId: match.id,
      similarityScore: parseFloat(similarityScore.toFixed(4)),
      previewImageUrl: match.preview_image_url,
      metadata: match.metadata || {},
    });

  } catch (error) {
    request.log.error(error);
    const errorMessage = error.response ? error.response.data.detail : 'Internal Server Error';
    return reply.code(500).send({ error: errorMessage });
  }
};
