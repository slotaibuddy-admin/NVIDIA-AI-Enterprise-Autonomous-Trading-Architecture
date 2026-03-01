const https = require('node:https');

const apiKey = process.env.BYTEZ_KEY || 'YOUR_BYTEZ_KEY';

const options = {
  hostname: 'api.bytez.com',
  path: '/models/v2/list/models?task=chat',
  method: 'GET',
  headers: {
    Authorization: apiKey,
  },
};

const req = https.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    try {
      console.log(JSON.parse(data));
    } catch (err) {
      console.error('Failed to parse response:', err);
    }
  });
});

req.on('error', (err) => {
  console.error(err);
});

req.end();
