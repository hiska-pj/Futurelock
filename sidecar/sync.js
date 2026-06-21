// sync.js — shared 0G upload sidecar used by all three app prototypes.
// Usage: node sync.js push <path-to-file>
//
// This is the same working approach debugged in the Jumpscare app:
// getFlowContract(flowAddress, signer) + indexer.upload().

import 'dotenv/config';
import fs from 'fs';
import { ethers } from 'ethers';
import { Indexer, Batcher, getFlowContract } from '@0gfoundation/0g-storage-ts-sdk';

const RPC_URL = process.env.RPC_URL;
const INDEXER_RPC = process.env.INDEXER_RPC;

// A fixed stream ID works fine for these prototypes -- it's just a
// namespace, not a secret. Override via .env if you want a different one.
const STREAM_ID =
  process.env.STREAM_ID ||
  '0x0c2a2d101aba16831fd325bb3b20441dafc45a769f05ec4d7e5293ba45c5f1ba';

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    console.error(`Missing ${name} in .env — copy .env.example to .env and fill it in.`);
    process.exit(1);
  }
  return value;
}

async function getSigner() {
  const provider = new ethers.JsonRpcProvider(requireEnv('RPC_URL'));
  return new ethers.Wallet(requireEnv('PRIVATE_KEY'), provider);
}

/**
 * Pushes the contents of `filePath` to 0G storage under `key`.
 * This is the exact proven approach from the Jumpscare app:
 * getFlowContract(flowAddress, signer) + Batcher.streamDataBuilder.set()
 */
async function push(filePath, key) {
  if (!fs.existsSync(filePath)) {
    console.error(`Missing file: ${filePath}`);
    process.exit(1);
  }

  const signer = await getSigner();
  const indexer = new Indexer(requireEnv('INDEXER_RPC'));

  const raw = fs.readFileSync(filePath, 'utf8');

  const [nodes, nodeErr] = await indexer.selectNodes(1);
  if (nodeErr) {
    console.error('Node selection failed:', nodeErr);
    process.exit(1);
  }

  const status = await nodes[0].getStatus();
  const flowAddress = status?.networkIdentity?.flowAddress;
  if (!flowAddress) {
    throw new Error('flowAddress missing from node status');
  }

  const flow = getFlowContract(flowAddress, signer);
  const batcher = new Batcher(1, nodes, flow, RPC_URL);

  const keyBytes = Uint8Array.from(Buffer.from(key, 'utf8'));
  const valueBytes = Uint8Array.from(Buffer.from(raw, 'utf8'));
  batcher.streamDataBuilder.set(STREAM_ID, keyBytes, valueBytes);

  const [tx, batchErr] = await batcher.exec();

  if (batchErr) {
    console.error('Batch execution error:', batchErr);
    process.exit(1);
  }

  // Single machine-readable line so Python can parse it easily
  console.log('RESULT_JSON:' + JSON.stringify(tx));
}

const filePath = process.argv[3];
const key = process.argv[4] || 'entry';

if (process.argv[2] === 'push' && filePath) {
  push(filePath, key).catch((err) => {
    console.error(err);
    process.exit(1);
  });
} else {
  console.error('Usage: node sync.js push <file-path> [key-name]');
  process.exit(1);
}
