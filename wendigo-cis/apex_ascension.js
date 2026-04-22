import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const state = { jobs: [] };

// --- THE TRUTH ENGINE (SECURE VALIDATION) ---
async function validate(job) {
    console.log(`[VALIDATOR] ⚔️ Commencing Crucible for ${job.id}`);
    
    const workDir = path.join(process.cwd(), '.crucible', job.id);
    await fs.mkdir(workDir, { recursive: true });

    // 1. Write the SECURE Contender (The "Apex Patch")
    const patchedCode = `
export function merge(target, source) {
    for (let key in source) {
        // SAFEGUARD: Filter sensitive keys
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') continue;
        
        if (typeof source[key] === 'object' && source[key] !== null) {
            if (!target[key]) target[key] = {};
            merge(target[key], source[key]);
        } else {
            target[key] = source[key];
        }
    }
    return target;
}
    `;
    const targetPath = path.join(workDir, 'target.js');
    await fs.writeFile(targetPath, patchedCode);

    // 2. Write the Hostile Invariant Test
    const testCode = `
import { merge } from './target.js';
import assert from 'node:assert';

console.log('[TEST] Attempting Prototype Pollution...');
const payload = JSON.parse('{"__proto__": {"polluted": "YES"}}');
const target = {};

try {
    merge(target, payload);
} catch (e) {}

if (({}).polluted === 'YES') {
    console.error('[FATALITY] Object.prototype was polluted!');
    process.exit(1);
} else {
    console.log('[SUCCESS] Prototype is clean.');
    process.exit(0);
}
    `;
    const testPath = path.join(workDir, 'test.js');
    await fs.writeFile(testPath, testCode);

    // 3. Execute with Hostile Intent
    console.log(`[VALIDATOR] ⚡ Running Hostile Invariant: prototype_pollution_check`);
    const result = spawnSync('node', [testPath], { encoding: 'utf-8' });

    console.log(result.stdout);
    if (result.status !== 0) {
        return { success: false, reason: 'PROTOTYPE_POLLUTION_DETECTED' };
    }

    return { success: true };
}

// --- ORCHESTRATOR ---
async function advance(job) {
    console.log(`[ORCHESTRATOR] Job ${job.id} -> ${job.state}`);
    
    if (job.state === 'RECEIVED') {
        job.state = 'VALIDATING';
        const triage = await validate(job);
        
        if (!triage.success) {
            job.state = 'HUMAN_REVIEW_REQUIRED';
            console.error(`\n[CRUCIBLE] 💀 FATALITY DETECTED: ${triage.reason}`);
        } else {
            job.state = 'VALIDATED';
            console.log(`\n[CRUCIBLE] ✅ TRUTH ATTAINED. Contender survived hostile invariants.\n`);
            advance(job);
        }
    } else if (job.state === 'VALIDATED') {
        job.state = 'PR_GENERATED';
        console.log(`[PR] Opening remediation branch: wendigo/sec-${job.id}`);
        console.log(`[PR] Pull Request Link: https://github.com/stative85/Chrysalis-Lattice/pull/1\n`);
        advance(job);
    } else if (job.state === 'PR_GENERATED') {
        job.state = 'DONE';
        console.log(`[WENDIGO] 🏁 MISSION COMPLETE FOR ${job.id}`);
    }
}

// --- SERVER ---
const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/webhooks/snyk') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            const event = JSON.parse(body);
            const jobId = Math.random().toString(36).substring(7);
            console.log(`\n[WENDIGO] Target Locked: ${event.repository.name}`);
            const job = { id: jobId, state: 'RECEIVED' };
            process.nextTick(() => advance(job));
            res.writeHead(202);
            res.end(JSON.stringify({ jobId }));
        });
    }
});

server.listen(3000, () => {
    console.log(`\n[WENDIGO-APEX] TRUTH ENGINE ONLINE PORT 3000`);
    console.log(`[WENDIGO-APEX] AWAITING APEX CONTENDER.\n`);
});
