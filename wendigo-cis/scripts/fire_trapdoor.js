import http from 'node:http';

const payload = JSON.stringify({
  eventType: "security.alert",
  source: "snyk",
  repository: { name: "Chrysalis-Lattice" },
  alert: {
    vulnId: "SNYK-JS-PROTOTYPE-POLLUTION",
    targetFile: "neuro-engine/packages/utils/src/index.ts"
  }
});

const req = http.request({
  hostname: 'localhost',
  port: 3000,
  path: '/webhooks/snyk',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': payload.length
  }
}, (res) => {
  console.log(`[SIMULATOR] Status: ${res.statusCode}`);
});

req.write(payload);
req.end();
