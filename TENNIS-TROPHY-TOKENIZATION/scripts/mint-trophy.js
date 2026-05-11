const hre = require("hardhat");

async function main() {
  // Configuration - UPDATE THESE VALUES
  const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || "YOUR_DEPLOYED_CONTRACT_ADDRESS";
  const RECIPIENT_ADDRESS = process.env.RECIPIENT_ADDRESS || "RECIPIENT_WALLET_ADDRESS";
  const TOKEN_URI = process.env.TOKEN_URI || "ipfs://YOUR_METADATA_CID";
  
  // Trophy details - UPDATE THESE
  const TROPHY_DETAILS = {
    name: "1947 Championship Tennis Trophy",
    description: "Historic tennis trophy awarded annually since 1947. Features engraved names of all champions.",
    year: 1947,
    winners: [
      "1947 - [Winner Name]",
      "1948 - [Winner Name]",
      "1949 - [Winner Name]",
      // Add all winners here...
      "2024 - [Winner Name]"
    ],
    material: "Silver", // or "Gold", "Silver-plated", etc.
    currentCustodian: "[Current Owner/Custodian Name]"
  };

  console.log("Minting trophy NFT...");
  console.log("Contract:", CONTRACT_ADDRESS);
  console.log("Recipient:", RECIPIENT_ADDRESS);
  console.log("Token URI:", TOKEN_URI);

  const [deployer] = await hre.ethers.getSigners();
  console.log("Minting with account:", deployer.address);

  // Get contract instance
  const TrophyNFT = await hre.ethers.getContractFactory("TrophyNFT");
  const trophyNFT = TrophyNFT.attach(CONTRACT_ADDRESS);

  // Mint the trophy
  const tx = await trophyNFT.mintTrophy(
    RECIPIENT_ADDRESS,
    TOKEN_URI,
    TROPHY_DETAILS.name,
    TROPHY_DETAILS.description,
    TROPHY_DETAILS.year,
    TROPHY_DETAILS.winners,
    TROPHY_DETAILS.material,
    TROPHY_DETAILS.currentCustodian
  );

  console.log("Transaction sent:", tx.hash);
  
  const receipt = await tx.wait();
  console.log("Transaction confirmed in block:", receipt.blockNumber);

  // Parse the event to get token ID
  const event = receipt.logs.find(
    log => {
      try {
        const parsed = trophyNFT.interface.parseLog(log);
        return parsed && parsed.name === "TrophyMinted";
      } catch {
        return false;
      }
    }
  );

  if (event) {
    const parsedEvent = trophyNFT.interface.parseLog(event);
    const tokenId = parsedEvent.args.tokenId;
    console.log("\n✅ Trophy NFT minted successfully!");
    console.log("Token ID:", tokenId.toString());
    console.log("Owner:", RECIPIENT_ADDRESS);
    console.log("\nView on:");
    console.log(`- Etherscan: https://${hre.network.name}.etherscan.io/token/${CONTRACT_ADDRESS}?a=${tokenId}`);
    console.log(`- OpenSea: https://testnets.opensea.io/assets/${hre.network.name}/${CONTRACT_ADDRESS}/${tokenId}`);
  } else {
    console.log("\n✅ Trophy minted but couldn't parse token ID from events");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
