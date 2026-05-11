# 1947 Tennis Trophy Tokenization Project

## Overview
A complete blockchain prototype for tokenizing a real-world 1947 tennis trophy with all winner names engraved. This project demonstrates RWA (Real World Asset) tokenization from concept to deployed dApp.

## Project Architecture

```
Physical Trophy (1947) 
    ↓
IPFS Storage (Image + Metadata)
    ↓
ERC-721 Smart Contract (Ethereum/Polygon)
    ↓
dApp Frontend (Next.js + wagmi)
    ↓
Wallet Integration (MetaMask)
```

## Trophy Details
- **Year**: 1947
- **Sport**: Tennis
- **Type**: Championship Trophy
- **Winners**: Multiple years engraved (to be documented)
- **Material**: [To be specified]
- **Current Custodian**: [To be specified]

## Tech Stack
- **Smart Contracts**: Solidity + OpenZeppelin ERC-721
- **Development**: Hardhat
- **Storage**: IPFS (Pinata)
- **Frontend**: Next.js 14 + wagmi/viem
- **Network**: Ethereum Sepolia (testnet) → Polygon (mainnet)
- **Wallet**: MetaMask

## Project Phases

### Phase 1: Foundations
- [ ] Study blockchain & tokenization basics
- [ ] Deep dive into ERC-721 standard
- [ ] Research RWA tokenization examples
- [ ] Learn NFT metadata standards
- [ ] Review prototype architecture

### Phase 2: Quick Validation
- [ ] Set up IPFS storage (Pinata)
- [ ] Deploy test ERC-721 collection
- [ ] Mint sample trophy NFT
- [ ] View & verify token
- [ ] Create QR code link

### Phase 3: Development Environment
- [ ] Install Node.js, VS Code, Git
- [ ] Initialize Hardhat project
- [ ] Install OpenZeppelin Contracts
- [ ] Set up MetaMask & test ETH
- [ ] Configure Hardhat for Sepolia

### Phase 4: Smart Contract Development
- [ ] Create TrophyNFT.sol contract
- [ ] Add provenance features (events)
- [ ] Write deployment script
- [ ] Write basic tests
- [ ] Compile & test locally

### Phase 5: Metadata & IPFS
- [ ] Finalize trophy details & attributes
- [ ] Prepare trophy image
- [ ] Upload image to IPFS
- [ ] Create & upload JSON metadata
- [ ] Document all URIs

### Phase 6: Deploy & Test
- [ ] Deploy to local Hardhat network
- [ ] Deploy to Sepolia testnet
- [ ] Verify contract on Etherscan
- [ ] Mint trophy token on testnet
- [ ] Verify on explorers & OpenSea

### Phase 7: Frontend dApp
- [ ] Set up Next.js frontend
- [ ] Implement wallet connection
- [ ] Create mint interface
- [ ] Display owned trophies
- [ ] Add transfer functionality

### Phase 8: Physical-Digital Link
- [ ] Generate final QR code
- [ ] Add physical custody note
- [ ] Print & attach QR to trophy
- [ ] (Optional) Make it soulbound
- [ ] Document RWA representation

### Phase 9: Documentation
- [ ] Create project README
- [ ] Capture screenshots
- [ ] Update task tracker
- [ ] Prepare demo script

### Phase 10: Review & Next Steps
- [ ] Review challenges & solutions
- [ ] Identify improvements
- [ ] Plan extensions
- [ ] Celebrate & share

## Getting Started

```bash
# Clone and setup
git clone [repo-url]
cd tennis-trophy-tokenization

# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test

# Deploy to testnet
npx hardhat run scripts/deploy.js --network sepolia

# Start frontend
cd frontend
npm install
npm run dev
```

## Resources
- [Ethereum Learn](https://ethereum.org/learn)
- [ERC-721 Standard](https://ethereum.org/en/developers/docs/standards/tokens/erc-721)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts)
- [Hardhat Documentation](https://hardhat.org/docs)
- [wagmi Documentation](https://wagmi.sh)

## License
MIT

---
**Project Status**: 🚀 In Progress
**Last Updated**: 2026-05-11
