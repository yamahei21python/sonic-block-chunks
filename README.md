# sonic-block-chunks

GitHub Actions factory for sonic mainnet (measured chainId 0x92 = 146).

- `workflow_dispatch`: `first_block`, `last_block`, `mode` (`raw` / `ledger`)
- One job, 100-block loop (no matrix)
- `eth_getBlockByNumber(hex,true)` + `eth_getBlockReceipts`
- Asset `sonic_<first>_<last>.json.gz`; manifest `sonic_<first>_<last>.json.gz.manifest.json` with first/last/block_count/tx_count/bytes/sha256
- Tag `data-<first>-<last>` (base-compatible short form)
- Public RPC (measured): https://rpc.soniclabs.com,https://sonic-rpc.publicnode.com

No keys, no downloads, no database writes.
